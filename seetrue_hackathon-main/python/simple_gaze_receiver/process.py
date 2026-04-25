import cv2
import collections

VGA_W, VGA_H = 640, 480


class process:
    def __init__(self, shared_data, image_buffer_scene):
        print("enter main")
        self.shared_data = shared_data
        self.image_buffer_scene = image_buffer_scene
        self.gazeX_history = collections.deque(maxlen=10) # smooth gaze data by averaging over last 10 values
        self.gazeY_history = collections.deque(maxlen=10)
        self.fixation_status = False
        self.threshold_duration = 0.8
        self.already_sent = False
        self.current_event = "NA"

        self.fix_history = collections.deque(maxlen=10) # history of fixations

    def get_filtered_gaze(self):
        rawGazeX = self.shared_data["GazeX"].value * 640
        rawGazeY = self.shared_data["GazeY"].value * 480

        if rawGazeX != 0 or rawGazeY != 0:  # Add if both not 0
            self.gazeX_history.append(rawGazeX)
            self.gazeY_history.append(rawGazeY)

        if len(self.gazeX_history) == 0:  # return 0, if history length is 0
            return 0, 0

        filteredGazeX = sum(self.gazeX_history) / len(self.gazeX_history)
        filteredGazeY = sum(self.gazeY_history) / len(self.gazeY_history)
        return int(filteredGazeX), int(filteredGazeY)

    def run(self):
        print("enter run")

        cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Video", VGA_W * 2, VGA_H * 2)

        #thread loop
        while not self.shared_data["stop"].value:
            GazeX, GazeY = self.get_filtered_gaze()

            # update event status if there's a new event            
            # events: S(saccade), FB(fixation begin), FE(fixation end), 
            #         BB(blink begin), BE(blink end), 
            #         NA(eye not available), empty string for no update
            event_updated = False
            if not self.shared_data["eyeEvent"].value == "" and not self.shared_data["eyeEvent"].value == self.current_event:
                self.current_event = self.shared_data["eyeEvent"].value
                event_updated = True

            #add fixations to history
            if event_updated and self.current_event == "FB":
                self.fix_history.append((GazeX, GazeY))

            #green for fixation, red for saccades, blue for blinks
            color = (0, 0, 255) #red by default
            if self.current_event == "FB":
                color = (0, 255, 0) #green for fixations until another event
            elif self.current_event == "BB":
                color = (255, 0, 0) #blue for blinks

            # copy frame
            frame = self.image_buffer_scene.copy()
            # pupil size for gaze point radius
            r = int(self.shared_data["PupilSizeLeft"].value + self.shared_data["PupilSizeRight"].value) // 2  # pupil size for gaze point radius, scaled for better visibility

            # draw fixation history, yellow lines and small circles
            linestarted = False #skip trying the first coord
            for fix in self.fix_history:
                cv2.circle(frame, fix, 5, (0, 255, 255), 1) #yellow circles for fixation history
                if not linestarted:
                    linestarted = True
                else:
                    cv2.line(frame, prev_fix, fix, (0, 255, 255), 1) #yellow lines for fixation history
                prev_fix = fix

            # draw gaze point
            cv2.circle(frame, (GazeX, GazeY), r, color, 2)

            cv2.imshow("Video", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):  # q to exit
                self.shared_data["stop"].value = True
                print("Q key pressed. Stopping all processes...")
                break

        # clean up window
        cv2.destroyAllWindows()
        print("Process stopped.")
