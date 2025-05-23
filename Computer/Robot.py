import pygame
import socket
import copy
import time
import sys

pygame.init()

# TCP/IP settings 
robot_IP   = "192.168.1.143"
# robot_IP = "192.168.8.117"
robot_port = 12345
robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# windows settings
SCREEN_WIDTH = 295
SCREEN_HEIGHT = 420
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Robot')

# colors settings
color_background = (126, 126, 126)


class Robot:
    def __init__(self, delete_me):
        # Test
        self.delete_me = delete_me
        print("Delete this")

        # Connection
        self.connection_status = False
        self.tcpip_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.default_timeout = 2.0
        self.last_ping_timestamp = 0

        # Power
        self.battery_voltage = 0.0
        self.battery_percent = 0.0
        self.battery_power   = 0.0
        self.battery_current = 0.0

        # Drive
        self.motors = [0, 0, 0, 0]
        self.motors_speed_left  = 0
        self.motors_speed_right = 0

        # Sensors
        self.ultrasonic_distance = 0
        self.line_sensors = [0, 0, 0]

        # Camera
        self.torch_value = 0

        # Servo
        self.cam_servo_value = 0

        # Draw
        self.draw_position = [40, 100]

        # Colors
        self.color_wheel1 = (255, 255, 0)
        self.color_wheel2 = (50, 50, 50)
        self.color_body = (20, 20, 20)
        self.color_wheel_arrow = (0, 255, 0)

        self.color_text_dark  = (0, 0, 0)
        self.color_text_light = (255, 255, 255)

        # self.color_battery_text = (0, 0, 0)
        self.color_battery_text = (255, 255, 255)
        self.color_battery_border = (0, 0, 0)
        self.color_battery_background = (50, 50, 50)
        # self.color_battery_background = (126, 126, 126)
        # self.color_battery_power = (0, 255, 0) if (self.battery_percent > 20) else (255, 0, 0)
        self.color_battery_power = (60, 60, 60) # ???

        self.color_line_sensor_inactive = (255, 0, 0)   
        self.color_line_sensor_active = (255, 255, 255)           
        self.color_line_sensor_background = (70, 70, 70)

        self.data_types = {
            # Motors speed
            0x01: lambda value: self.handle_motor_speed_data("M", value),
            0x02: lambda value: self.handle_motor_speed_data("L", value),
            0x03: lambda value: self.handle_motor_speed_data("R", value),

            # Motor direction
            0x04: lambda value: self.handle_data_motors_direction(value),
            0x05: lambda value: self.handle_cam_servo_value(value),

            # Robot sensors
            0x0A: lambda value: self.handle_line_sensor_data("L", value),
            0x0B: lambda value: self.handle_line_sensor_data("M", value),  
            0x0C: lambda value: self.handle_line_sensor_data("R", value),
            0x0D: lambda value: self.handle_ultrasonic_sensor_data(value),
            0x0E: lambda value: self.handle_obstacle_detection(value),

            # Robot power
            0x10: lambda value: self.handle_battery_voltage_data(value),
            0x11: lambda value: self.handle_battery_power_data(value),   
            0x12: lambda value: self.handle_battery_current_data(value), 

            # Robot state
            0xF2: lambda value: self.handle_torch_data(value),
            0xF0: lambda value: self.handle_emergency_stop(value),
            # 0xFF command ping
        }

    def __str__(self):
        return (
            f"Robot:\n"
            f"  Battery:    {self.battery_voltage:.2f} V ({self.battery_percent:.1f}%)\n"
            f"  Motors:     {self.motors}\n"
        )

    # Comunnication with robot
    def open_TCPIP_connection(self, ip: str, port: str) -> None:
        try:
            self.tcpip_client.settimeout(self.default_timeout)
            self.tcpip_client.connect((ip, port))
            self.connection_status = True
            print("Connected!")

        except socket.timeout:
            print(f"Nie udało się nawiązać połączenia z {ip}:{port} - przekroczono limit czasu.")
            return None
        
        except ConnectionRefusedError:
            print(f"Połączenie z {ip}:{port} zostało odrzucone.")
            return None
        
        except Exception as e:
            print(f"Błąd połączenia: {e}")
            return None
            
    def ping_robot(self) -> float: 
        # if (self.connection_status == False):
        #     print("Robot not connected!")
        #     # self.connection_status = False
        #     return -1

        try:
            self.tcpip_client.settimeout(5.0)

            start_timestamp = time.time()

            # self.tcpip_client.sendall(b"Ping")
            self.clear_recv_buffer(self.tcpip_client) 
            self.tcpip_client.sendall(bytes([0xCC, 0xFF, 0x69, 0x33])) #I = 0x69, I bo pIng

            data = b""
            while (len(data) < 4):
                # print(len(data))
                chunk = self.tcpip_client.recv(4 - len(data)) 
                if not chunk:  
                    raise ValueError("No data received...")
                data += chunk

            # if (data == b"Pong"):
            if (data == bytes([0xCC, 0xFF, 0x6F, 0x33])): #O = 0x6F, O bo pOng
                end_timestamp = time.time()
                ping_time = end_timestamp - start_timestamp
                print(f"Ping time: {round(ping_time,3)}s")
                self.connection_status = True
                return ping_time
            else:
                self.connection_status = False
                raise ValueError("Wrong response for ping: " + repr(data))
            
        except socket.timeout:
            print("Lost connection wiht robot!")
            self.connection_status = False
            return -1
        
        except Exception as e:
            print(f"Error during ping: {e}")
            self.connection_status = False
            return -1
        
        finally:
            self.tcpip_client.settimeout(self.default_timeout)
            self.last_ping_timestamp = time.time()          

    def clear_recv_buffer(self, sock):
        sock.setblocking(False)
        try:
            while True:
                data = sock.recv(1024)
                if not data:
                    break
        except BlockingIOError:
            pass
        finally:
            sock.setblocking(True)

    def check_for_data_from_TCPIP(self) -> None:
        # print("Looking for data...")
        try:
            self.tcpip_client.settimeout(0.0)
            peeked_data = self.tcpip_client.recv(4096, socket.MSG_PEEK)

            if (len(peeked_data) >= 4):
                start_bit = self.tcpip_client.recv(1)

                if (start_bit != bytes([0xCC])):
                    print("Wrong start bit")
                    return

                # print("New data!")
                data = start_bit + self.tcpip_client.recv(3)

                if (data[3] != 0x33):
                    print("Wrong end bit")
                    return

                self.handle_TCPIP_data(data)

        except BlockingIOError:
            # Brak danych w buforze – wszystko OK
            pass
        except Exception as e:
            print(f"Error in check_for_data_from_TCPIP: {e}")
        finally:
            self.tcpip_client.settimeout(self.default_timeout)

    # Handle data
    def handle_TCPIP_data(self, data) -> None:
        if (len(data) != 4):
            raise ValueError("Bad array length")
    
        if not all(isinstance(byte, int) for byte in data):
            raise TypeError("Each element in data should be an integer.")
        
        if not all(0 <= byte <= 255 for byte in data):
            raise ValueError("Each byte should be in the range 0-255.")
        
        # print(f"Data from TCP/IP: {data[0]}, {data[1]}, {data[2]}, {data[3]}")

        action = self.data_types.get(data[1], None)  
        if action:
            action(data[2])
        else:
            raise ValueError(f"Unknown data type: {data[1]}")

    def handle_motor_speed_data(self, which: str, value: int) -> None:
        if value < 0 or value > 255:
            raise ValueError(f"Motor speed value must be between 0 and 255.")
        
        match which:
            case "L":
                print(f"Handling left motor speed: {value}")
                self.motors_speed_left = value
            case "M":
                print(f"Handling both motors speed: {value}")
                self.motors_speed_left = value
                self.motors_speed_right = value
            case "R":
                print(f"Handling right motor speed: {value}")
                self.motors_speed_right = value
            case _:
                raise ValueError(f"Unknown motor type: {which}")

#TODO 
    def handle_data_motors_direction(self, value: int) -> None:
        print("Handling data motors direction")
        # self.motors_confirmed = value

    def handle_cam_servo_value(self, value: int) -> None:
        print("Handling cam servo value")
        
        if not (0 <= value <= 255):
            raise ValueError(f"cam servo value {value} out of range (0-255)")
        
        self.cam_servo_value = value

    def handle_line_sensor_data(self, which: str, value: int) -> None:
        if not (0 <= value <= 255):
            raise ValueError(f"Invalid sensor value {value}. Must be between 0 and 255.")

        match (which):
            case "L":
                # print(f"Left line sensor: {value}")
                self.line_sensors[0] = value
            case "M":
                # print(f"Middle line sensor: {value}")
                self.line_sensors[1] = value
            case "R":
                # print(f"Right line sensor: {value}")
                self.line_sensors[2] = value
            case _:
                raise ValueError("Wrong line sensor!")

    def handle_ultrasonic_sensor_data(self, value: int) -> None:
        # print(f"Ultrasonic sensor distance: {value}")
        self.ultrasonic_distance = value

    def handle_obstacle_detection(self, value) -> None:
        print("Obstacle detected")
        self.handle_ulstrasonic_sensor_data(value)

    def handle_battery_voltage_data(self, value: int) -> None:
        min_voltage_for_percent = 6.0   # 0% 
        max_voltage_for_percent = 8.4   # 100% 
        voltage_min_raw = 5.85          # value=0
        voltage_max_raw = 8.40          # value=255

        if not (0 <= value <= 255):
            raise ValueError(f"Battery value {value} out of range (0-255)")

        voltage = voltage_min_raw + (value / 255) * (voltage_max_raw - voltage_min_raw)

        if voltage <= min_voltage_for_percent:
            percent = 0
        elif voltage >= max_voltage_for_percent:
            percent = 100
        else:
            percent = ((voltage - min_voltage_for_percent) / (max_voltage_for_percent - min_voltage_for_percent)) * 100

        self.battery_voltage = round(voltage, 2)
        self.battery_percent = round(percent, 2)

        self.color_battery_power = (0, 255, 0) if (self.battery_percent > 20) else (255, 0, 0)

    def handle_battery_power_data(self, value: int) -> None:
        max_power_mW = 5500  # 5.5 W max
        if not (0 <= value <= 255):
            raise ValueError(f"Battery power value {value} out of range (0-255)")

        power_mW = (value / 255) * max_power_mW
        power_W = power_mW / 1000  # zamiana na W
        
        self.battery_power = round(power_W, 3)  # np. 2.345 W

    def handle_battery_current_data(self, value: int) -> None:
        max_current_mA = 1100  # max 1100 mA
        if not (0 <= value <= 255):
            raise ValueError(f"Battery current value {value} out of range (0-255)")

        current_mA = (value / 255) * max_current_mA
        current_A = current_mA / 1000  # zamiana na A
        
        self.battery_current = round(current_A, 3)  # np. 0.875 A}

    def handle_torch_data(self, value: int) -> None:
        print("Handle torch state")

        if not (0 <= value <= 255):
            raise ValueError(f"Torch value {value} out of range (0-255)")
        
        self.torch_value = value

    def handle_emergency_stop(self, value: int) -> None:
        if (value == 0):
            raise RuntimeError("Robot make emernency stop")
        else:
            print(f"Robot make emergency stop: {value}")

    # Send data
    def send_commands_to_robot(self, num_of_command: int, data_to_send: int) -> bool:
        if (self.connection_status == False):
            print("Send Error! Robot not connected")
            return False
        
        try:
            data_bytes = bytes([0xCC, num_of_command, data_to_send, 0x33])
            self.tcpip_client.sendall(data_bytes)
            return True

        except (socket.error, Exception) as e:
            print(f"Send error: {e}")
            self.connection_status = False
            return False

    def send_motors_speed(self, speed, n) -> None:
        if (n == 0):
            print("Send speed M: ", speed)
            # self.motors_speed_left  = speed
            # self.motors_speed_right = speed
            self.send_commands_to_robot(0x01, speed)
        elif (n == 1):
            print("Send speed L: ", speed)
            # self.motors_speed_left = speed
            self.send_commands_to_robot(0x02, speed)
        elif (n == 2):
            print("Send speed R: ", speed)
            # self.motors_speed_right = speed
            self.send_commands_to_robot(0x03, speed)
        else:
            print("Send Error! Wrong arguments")
            return
        
    def send_motor_commands_to_robot(self, motors_rotation) -> None:
        if not (isinstance(motors_rotation, list)) or (len(motors_rotation) != 4):
            raise ValueError("motors_rotation must be a list of 4 integers representing motor directions.")
    
        if not all(motor in [-1, 0, 1] for motor in motors_rotation):
            raise ValueError("Each motor in motors_rotation must be -1, 0, or 1.")

        # print("Send dir: ", motors_rotation)
        byte_to_send = self.__motor_rotation_to_byte(motors_rotation)
        self.send_commands_to_robot(0x04, byte_to_send)

    def send_cam_servo_value(self, value: int) -> None:
        if not (0 <= value <= 255):
            raise ValueError(f"Can't send: Cam servo value {value} out of range (0-255)")
        
        self.send_commands_to_robot(0x05, value)

    # Controll 
    def move_robot_in_direction(self, direction: str) -> None:
        motors_dir = self.__direction_to_motors(direction)
        
        if motors_dir is None:
            raise ValueError(f"Unknown direction: {direction}")

        self.motors = motors_dir
        self.send_motor_commands_to_robot(motors_dir)
    
    def change_wheel_rotation(self, wheel_index: int, change: int) -> None:
        if wheel_index not in [0, 1, 2, 3]:
            raise ValueError(f"Invalid wheel index: {wheel_index}. It must be 0, 1, 2, or 3.")
    
        if change not in [-1, 1]:
            raise ValueError(f"Invalid change value: {change}. It must be -1 or 1.")

        motor_direction = self.motors[wheel_index] + change

        if (motor_direction < -1):
            motor_direction = -1
        elif (motor_direction > 1):
            motor_direction = 1

        self.motors[wheel_index] = motor_direction
        self.send_motor_commands_to_robot(self.motors)

    def change_cam_servo_value(self, value: int) -> None:
        new_value = self.cam_servo_value + value

        if (new_value < 0):
            new_value = 0
        
        if (new_value > 180):
            new_value = 180

        print(f"Change cam servo value to {new_value}")
        self.send_commands_to_robot(0x05, new_value)
        self.cam_servo_value = new_value

    def change_torch(self) -> None:
        if (self.torch_value == 0):
            print(f"set torch to 255")
            self.send_commands_to_robot(0x20, 255)
        else:
            print(f"set torch to 0")
            self.send_commands_to_robot(0x20, 0)

    # Help functions
    def __motor_rotation_to_byte(self, motors_rotation) -> int:
        if (len(motors_rotation) != 4):
            raise ValueError("Bad array lenght")
        
        #wh arr robot byte    arr
        #FL [0] = M1 [8 7] -> [0 1]
        #FR [1] = M3 [2 3] -> [6 5]
        #BL [2] = M2 [6 5] -> [2 3]
        #BR [3] = M4 [1 4] -> [7 4] 

        # bit_positions = [(0, 1), (6, 5), (2, 3), (7, 4)]
        bit_positions = [(7, 6), (1, 2), (5, 4), (0, 3)]

        byte_to_send = 0
        for i, (fwd, bwd) in enumerate(bit_positions):
            if motors_rotation[i] > 0:
                byte_to_send |= (1 << fwd)
            elif motors_rotation[i] < 0:
                byte_to_send |= (1 << bwd)

        if ((byte_to_send < 0) or (byte_to_send > 255)):
            raise ValueError("Value is out of the byte range (0-255)")

        return byte_to_send
    
    def __direction_to_motors(self, direction: str) -> list[int] | None:
        cases = {
            "STOP":            [0,  0,  0,  0],
            "FORWARD":         [1,  1,  1,  1],
            "BACKWARD":        [-1, -1, -1, -1],
            "RIGHT":           [1,  -1, -1, 1],    
            "LEFT":            [-1, 1,  1,  -1],     
            "TURN_LEFT":       [0,  1,  0,  1],
            "TANK_LEFT":       [-1, 1,  -1, 1],
            "TURN_RIGHT":      [1,  0,  1,  0],
            "TANK_RIGHT":      [1,  -1, 1,  -1],
            "FORWARD_RIGHT":   [1,  0,  0,  1],  
            "FORWARD_LEFT":    [0,  1,  1,  0],  
            "BACKWARD_RIGHT":  [0,  -1, -1, 0], 
            "BACKWARD_LEFT":   [-1, 0,  0,  -1], 
            "SPIN_BACK_LEFT":  [0,  0,  -1,  1],
            "SPIN_BACK_RIGHT": [0,  0,  1,  -1],
            "SPIN_FRONT_LEFT": [-1,  1, 0,  0],
            "SPIN_FRONT_RIGHT":[1, -1,  0,  0]
        }

        return cases.get(direction, None)

    # Draw robot
    def update_draw_position(self, start_pix: tuple[int, int]) -> None:
        self.draw_position = start_pix

    def draw(self, screen) -> None:
        font_type = 'SF Pro'
        # font_type = 'Arial'
        font       = pygame.font.SysFont(font_type, 36)
        font_small = pygame.font.SysFont(font_type, 24)
        # font       = pygame.font.Font( 36)
        # font_small = pygame.font.Font(None, 24)

        wheel_size = (40, 80)
        wheel_base = (175, 150)

        # Robot body
        self.__draw_body(screen, wheel_size, wheel_base)
        wheels_array = self.__draw_wheels(screen, wheel_size, wheel_base)
        self.__draw_arrows(screen, wheels_array)
        self.__draw_keys(screen, font, wheels_array)
        self.__draw_motors_speed(screen, font, wheels_array, wheel_base)

        # Connection
        self.__draw_connection_status(screen, font, self.connection_status)

        # Sensors
        self.__draw_ultrasonic_distance(screen, font, self.ultrasonic_distance)
        self.__draw_battery(screen, font_small)
        self.__draw_line_sensors(screen, 128)

    # Draw robot body
    def __draw_body(self, screen, wheel_Size: tuple[int, int], wheel_Base: tuple[int, int]) -> None:
        body_position = (
            self.draw_position[0] + wheel_Size[0] + 10, 
            self.draw_position[1]
        )
        body_size = (
            wheel_Base[0] - wheel_Size[0] - 19, #- 20,
            wheel_Base[1] + wheel_Size[1]
        )
        pygame.draw.rect(screen, self.color_body, (body_position, body_size))

    def __draw_wheels(self, screen, wheel_Size: tuple[int, int], wheel_Base: tuple[int, int]) -> list[pygame.Rect]:
        wheel_FL = pygame.Rect(self.draw_position[0], self.draw_position[1], wheel_Size[0], wheel_Size[1])
        wheel_FR = pygame.Rect(self.draw_position[0] + wheel_Base[0], self.draw_position[1], wheel_Size[0], wheel_Size[1])
        wheel_BL = pygame.Rect(self.draw_position[0], self.draw_position[1] + wheel_Base[1], wheel_Size[0], wheel_Size[1])
        wheel_BR = pygame.Rect(self.draw_position[0] + wheel_Base[0], self.draw_position[1] + wheel_Base[1], wheel_Size[0], wheel_Size[1])

        wheels_array = [wheel_FL, wheel_FR, wheel_BL, wheel_BR]

        for wheel in wheels_array:
            pygame.draw.rect(screen, self.color_wheel1, wheel)

        # FL
        points = [
            (wheel_FL[0], wheel_FL[1]), 
            (wheel_FL[0], wheel_FL[1] + 20), 
            (wheel_FL[0] + wheel_Size[0], wheel_FL[1] + 40),
            (wheel_FL[0] + wheel_Size[0], wheel_FL[1] + 20)]
        pygame.draw.polygon(screen, self.color_wheel2, points)
        points = [
            (wheel_FL[0], wheel_FL[1] + 40), 
            (wheel_FL[0], wheel_FL[1] + 60), 
            (wheel_FL[0] + wheel_Size[0], wheel_FL[1] + 80),
            (wheel_FL[0] + wheel_Size[0], wheel_FL[1] + 60)]
        pygame.draw.polygon(screen, self.color_wheel2, points)

        # FR
        points = [
            (wheel_FR[0] + wheel_Size[0], wheel_FR[1]), 
            (wheel_FR[0] + wheel_Size[0], wheel_FR[1] + 20), 
            (wheel_FR[0], wheel_FR[1] + 40),
            (wheel_FR[0], wheel_FR[1] + 20)]
        pygame.draw.polygon(screen, self.color_wheel2, points)
        points = [
            (wheel_FR[0] + wheel_Size[0], wheel_FR[1] + 40), 
            (wheel_FR[0] + wheel_Size[0], wheel_FR[1] + 60), 
            (wheel_FR[0], wheel_FR[1] + 80),
            (wheel_FR[0], wheel_FR[1] + 60)]
        pygame.draw.polygon(screen, self.color_wheel2, points)

        # BL
        points = [
            (wheel_BL[0] + wheel_Size[0], wheel_BL[1]), 
            (wheel_BL[0] + wheel_Size[0], wheel_BL[1] + 20), 
            (wheel_BL[0], wheel_BL[1] + 40),
            (wheel_BL[0], wheel_BL[1] + 20)]
        pygame.draw.polygon(screen, self.color_wheel2, points)
        points = [
            (wheel_BL[0] + wheel_Size[0], wheel_BL[1] + 40), 
            (wheel_BL[0] + wheel_Size[0], wheel_BL[1] + 60), 
            (wheel_BL[0], wheel_BL[1] + 80),
            (wheel_BL[0], wheel_BL[1] + 60)]
        pygame.draw.polygon(screen, self.color_wheel2, points)

        # BR
        points = [
            (wheel_BR[0], wheel_BR[1]), 
            (wheel_BR[0], wheel_BR[1] + 20), 
            (wheel_BR[0] + wheel_Size[0], wheel_BR[1] + 40),
            (wheel_BR[0] + wheel_Size[0], wheel_BR[1] + 20)]
        pygame.draw.polygon(screen, self.color_wheel2, points)
        points = [
            (wheel_BR[0], wheel_BR[1] + 40), 
            (wheel_BR[0], wheel_BR[1] + 60), 
            (wheel_BR[0] + wheel_Size[0], wheel_BR[1] + 80),
            (wheel_BR[0] + wheel_Size[0], wheel_BR[1] + 60)]
        pygame.draw.polygon(screen, self.color_wheel2, points)

        return wheels_array

    def __draw_arrows(self, screen, wheels_array: list[pygame.Rect]) -> None:
        arrow_down_points = [
            [10, 0], 
            [10, 20],
            [0, 20],
            [15, 35],
            [30, 20],
            [20, 20],
            [20, 0]
        ]
        arrow_up_points = [
            [15, 0],
            [0, 15],
            [10, 15],
            [10, 35],
            [20, 35],
            [20, 15],
            [30, 15]
        ]

        for wh in range(0, 4):
            if (self.motors[wh] > 0):
                #forward
                arrow = copy.deepcopy(arrow_up_points)
                for point in arrow:
                    point[0] += wheels_array[wh][0] + 5
                    point[1] += wheels_array[wh][1] + 20
                
                pygame.draw.polygon(screen, self.color_wheel_arrow, arrow)

            elif (self.motors[wh] < 0):
                #backward
                arrow = copy.deepcopy(arrow_down_points)
                for point in arrow:
                    point[0] += wheels_array[wh][0] + 5
                    point[1] += wheels_array[wh][1] + 20
                
                pygame.draw.polygon(screen, self.color_wheel_arrow, arrow)

            else:
                #stop
                pass

    def __draw_keys(self, screen, font, wheels_array: list[pygame.Rect], font_height: int = 20) -> None:
        all_keys_to_draw = [
            # Pierwsze koło (przednie lewe) - Y nad H, przesunięte w lewo
            (font.render("Y", True, self.color_text_light), (wheels_array[0][0] - 20, wheels_array[0][1])),
            (font.render("H", True, self.color_text_light), (wheels_array[0][0] - 20, wheels_array[0][1] + wheels_array[0][3] - font_height)),

            # Drugie koło (przednie prawe) - U nad J, przesunięte w prawo o 5 pikseli
            (font.render("U", True, self.color_text_light), (wheels_array[1][0] + wheels_array[1][2] + 5, wheels_array[1][1])),
            (font.render("J", True, self.color_text_light), (wheels_array[1][0] + wheels_array[1][2] + 5, wheels_array[1][1] + wheels_array[1][3] - font_height)),

            # Trzecie koło (tylne lewe) - I nad K, przesunięte w lewo
            (font.render("I", True, self.color_text_light), (wheels_array[2][0] - 15, wheels_array[2][1])),
            (font.render("K", True, self.color_text_light), (wheels_array[2][0] - 20, wheels_array[2][1] + wheels_array[2][3] - font_height)),

            # Czwarte koło (tylne prawe) - O nad L, przesunięte w prawo o 5 pikseli
            (font.render("O", True, self.color_text_light), (wheels_array[3][0] + wheels_array[3][2] + 5, wheels_array[3][1])),
            (font.render("L", True, self.color_text_light), (wheels_array[3][0] + wheels_array[3][2] + 5, wheels_array[3][1] + wheels_array[3][3] - font_height)),
        ]

        for key in all_keys_to_draw:
            screen.blit(key[0], key[1])

    def __draw_motors_speed(self, screen, font, wheels_array: list[pygame.Rect], wheel_base: tuple[int, int]) -> None:
        text_speed_left  = f"{self.motors_speed_left}"
        text_speed_right = f"{self.motors_speed_right}"

        position_left  = [wheels_array[0][0], wheels_array[0][1] + wheels_array[0][2] + (wheel_base[1]) / 2 ]
        position_right = [wheels_array[1][0], position_left[1]]
        
        text_to_render_left  = font.render(text_speed_left,  True, self.color_text_dark)
        text_to_render_right = font.render(text_speed_right, True, self.color_text_dark)

        text_rect_left = text_to_render_left.get_rect(center = (position_left[0] + (wheels_array[0][2] / 2), position_left[1]))
        text_rect_right = text_to_render_right.get_rect(center = (position_right[0] + (wheels_array[2][2] / 2), position_right[1]))

        screen.blit(text_to_render_left, text_rect_left)
        screen.blit(text_to_render_right, text_rect_right)

    # Draw sensors
    def __draw_ultrasonic_distance(self, screen, font, distance: int = 0) -> None:
        # if distance is None:
        #     distance_text = "--- cm"
        if (distance < 0):
            distance_text = "000 cm"
        elif (distance > 250):
            distance_text = "inf cm"
        else:
            distance_text = f"{distance:03d} cm"

        text_to_render = font.render(distance_text, True, self.color_text_dark)
        text_rect = text_to_render.get_rect(center = (self.delete_me / 2, self.draw_position[1] - 30 + text_to_render.get_height() / 2))
        screen.blit(text_to_render, text_rect)

    def __draw_line_sensors(self, screen, threshold: int = 128) -> None:
        x = self.draw_position[0] + 83
        y = self.draw_position[1] + 25
        radius = 7
        spacing = 25
        border = 5

        line_sensors_width = (spacing + radius + border) * 2
        line_sensors_height = (radius + border) * 2 
        background_rect = pygame.Rect(x - radius - border, y - radius - border, line_sensors_width, line_sensors_height)
        pygame.draw.rect(screen, self.color_line_sensor_background, background_rect, border_radius = 10)

        for idx in range(3):
            center_x = x + idx * spacing
            center = (center_x, y)

            value = self.line_sensors[idx]

            analog_color_value = int((value / 255) * 255)
            # analog_color_value = 255 - int((value / 255) * 255)
            fill_color = (analog_color_value, analog_color_value, analog_color_value)
            pygame.draw.circle(screen, fill_color, center, radius)

            if value >= threshold:
                border_color = self.color_line_sensor_active
            else:
                border_color = self.color_line_sensor_inactive

            pygame.draw.circle(screen, border_color, center, radius, width = 3)

    def __draw_battery(self, screen, font) -> None:
        battery_width = 112
        battery_height = 40
        border_thickness = 5
        terminal_width = 4
        terminal_height = 20
        content_height = battery_height - 2 * border_thickness

        battery_draw_position = [50, 250]
        battery_draw_position[0] += self.draw_position[0]
        battery_draw_position[1] += self.draw_position[1]

        pygame.draw.rect(screen, self.color_battery_border, (battery_draw_position[0], battery_draw_position[1], battery_width, battery_height))
        pygame.draw.rect(screen, self.color_battery_background, (battery_draw_position[0] + border_thickness, battery_draw_position[1] + border_thickness, battery_width - 2 * border_thickness, content_height))
        
        fill_width = (self.battery_percent / 100) * (battery_width - 2 * border_thickness)
        pygame.draw.rect(screen, self.color_battery_power, (battery_draw_position[0] + border_thickness, battery_draw_position[1] + border_thickness, fill_width, content_height))
        pygame.draw.rect(screen, self.color_battery_border, (battery_draw_position[0] + battery_width, battery_draw_position[1] + (battery_height - terminal_height) // 2, terminal_width, terminal_height))

        # text_to_render = font.render(f"{self.battery_percent:.0f}% {self.battery_voltage:.2f}V", True, self.color_battery_text)
        # # text_rect = text_to_render.get_rect(center = (start_Pix[0] + text_to_render.get_width() / 2, start_Pix[1] + text_to_render.get_height()))
        # text_rect = text_to_render.get_rect(center = (battery_draw_position[0] + battery_width / 2, battery_draw_position[1] + battery_height / 2))
        # screen.blit(text_to_render, text_rect)

        # V / % 
        text_voltage = font.render(f"{self.battery_percent:.0f}% {self.battery_voltage:.2f}V", True, self.color_battery_text)
        text_voltage_rect = text_voltage.get_rect(center=(battery_draw_position[0] + battery_width / 2, battery_draw_position[1] + battery_height / 2))
        screen.blit(text_voltage, text_voltage_rect)

        # W / A
        power_text = font.render(f"{self.battery_power:.2f}W {self.battery_current:.2f}A", True, self.color_battery_text)
        power_text_rect = power_text.get_rect(center=(battery_draw_position[0] + battery_width / 2, battery_draw_position[1] + battery_height + 15))  # 15px pod baterią
        screen.blit(power_text, power_text_rect)

    # Draw connection
    def __draw_connection_status(self, screen, font, connection_status: bool) -> None:
        #print("TODO: check connection status!!!!!!!!!!")

        connection_status_text = "Connected" if connection_status else "Disconnected"   
        text_to_render = font.render(connection_status_text, True, (0, 0, 0))
        text_rect = text_to_render.get_rect(center = (self.delete_me / 2, 10 + text_to_render.get_height() / 2))
        screen.blit(text_to_render, text_rect)
# END ROBOT

def check_keyboard(key_event, robot):
    # Separate check for speed and safety
    if key_event == pygame.K_SPACE:
        robot.move_robot_in_direction("STOP")
        return

    action = keyboard_actions.get(key_event)  
    if action:
        # robot.send_motor_commands_to_robot(action())
        action()

keyboard_actions = {
    # Motors speed
    pygame.K_1:     lambda: robot.send_motors_speed(0, 1),
    pygame.K_2:     lambda: robot.send_motors_speed(128, 1),
    pygame.K_3:     lambda: robot.send_motors_speed(255, 1),
    pygame.K_4:     lambda: robot.send_motors_speed(0, 2),
    pygame.K_5:     lambda: robot.send_motors_speed(128, 2),
    pygame.K_6:     lambda: robot.send_motors_speed(255, 2),
    pygame.K_7:     lambda: robot.send_motors_speed(0, 0),
    pygame.K_8:     lambda: robot.send_motors_speed(128, 0),
    pygame.K_9:     lambda: robot.send_motors_speed(255, 0),

    # Motors direction
    pygame.K_y:     lambda: robot.change_wheel_rotation(0, +1),
    pygame.K_h:     lambda: robot.change_wheel_rotation(0, -1),
    pygame.K_u:     lambda: robot.change_wheel_rotation(1, +1),
    pygame.K_j:     lambda: robot.change_wheel_rotation(1, -1),
    pygame.K_i:     lambda: robot.change_wheel_rotation(2, +1),
    pygame.K_k:     lambda: robot.change_wheel_rotation(2, -1),
    pygame.K_o:     lambda: robot.change_wheel_rotation(3, +1),
    pygame.K_l:     lambda: robot.change_wheel_rotation(3, -1),

    # Robot movement
    pygame.K_w:     lambda: robot.move_robot_in_direction("FORWARD"),
    pygame.K_s:     lambda: robot.move_robot_in_direction("BACKWARD"),
    pygame.K_a:     lambda: robot.move_robot_in_direction("LEFT"),
    pygame.K_d:     lambda: robot.move_robot_in_direction("RIGHT"),
    pygame.K_q:     lambda: robot.move_robot_in_direction("TANK_LEFT"),
    pygame.K_e:     lambda: robot.move_robot_in_direction("TANK_RIGHT"),
    pygame.K_r:     lambda: robot.move_robot_in_direction("FORWARD_LEFT"),
    pygame.K_t:     lambda: robot.move_robot_in_direction("FORWARD_RIGHT"),
    pygame.K_f:     lambda: robot.move_robot_in_direction("BACKWARD_LEFT"),
    pygame.K_g:     lambda: robot.move_robot_in_direction("BACKWARD_RIGHT"),
    # pygame.K_SPACE: lambda: robot.move_robot_in_direction("STOP")
    pygame.K_KP1:   lambda: robot.move_robot_in_direction("SPIN_BACK_LEFT"),
    pygame.K_KP3:   lambda: robot.move_robot_in_direction("SPIN_BACK_RIGHT"),
    pygame.K_KP7:   lambda: robot.move_robot_in_direction("SPIN_FRONT_LEFT"),
    pygame.K_KP9:   lambda: robot.move_robot_in_direction("SPIN_FRONT_RIGHT"),

    # Cam servo
    pygame.K_KP8:   lambda: robot.change_cam_servo_value(+10),
    pygame.K_KP2:   lambda: robot.change_cam_servo_value(-10),

    # Others
    pygame.K_KP5:   lambda: robot.change_torch(),
    pygame.K_p:     lambda: robot.ping_robot()
}

print("Start\n")

print("TODO: dwonload servomoror value")
print("TODO: delete screen_width from robot.__init__")
print("TODO finish handle_Data_Motors_Direction()")

# Changes: 
#   - handling emergency stop

run = True

# motors = [0, 0, 0, 0] #delete this -----------------------------------------------------------------
draw_robot_position = [40, 100]

robot = Robot(SCREEN_WIDTH) #fix this --------------------------------------------------------
robot.update_draw_position(draw_robot_position)
robot.handle_battery_voltage_data(135)
robot.ultrasonic_distance = 158
# robot.line_sensors = [0, 120, 255]

robot.open_TCPIP_connection(robot_IP, robot_port)
# robot.ping_robot()

while run:
    screen.fill(color_background)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        elif event.type == pygame.KEYDOWN:  
            check_keyboard(event.key, robot)

    current_time = time.time()
    if (current_time - robot.last_ping_timestamp > 10):
        pass
        # robot.ping_robot()
    
    # robot.ping_robot()
    robot.check_for_data_from_TCPIP()
    robot.draw(screen)

    # update pixels
    pygame.display.flip()

# while end 
robot_socket.close()
robot.connection_status = False
pygame.quit()