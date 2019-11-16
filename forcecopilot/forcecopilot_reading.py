import socket
import time


class TestIO:

    def __init__(self):
        # self.ipAddress = "10.20.8.136"
        self.ipAddress = "10.20.0.194"
        self.port = 63350

    def queryServer(self, query):
        """
        Private method that sends a command and returns the server's response
        in a readable fashion

        1- Creates a TCP socket with the robot on the port 63 350.
        2- Encode and execute the given query.
        3- Store the result
        4- Close the socket
        5- Return the server's answer.

        Args:
            query (String): Query to send to the server.

        Returns:

        """
        # Create the socket
        tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to the server
        tcpSocket.connect((self.ipAddress, self.port))

        # Run the query
        tcpSocket.sendall(query.encode())

        try:
            # Receive the result
            data = tcpSocket.recv(1024)
        except Exception as e:
            print(str(e))
        finally:
            tcpSocket.close()

        # Return the formatted value
        return data


if __name__ == '__main__':
    """
        GET SNU returns the serial number as string formatted int8 array
        GET FWV returns the firmware version as string formatted int8 array
        GET PYE returns the production year as string formatted int8 array
        SET ZRO This calibrates the sensor's current readings to zero then returns "Done"
    """

    test = TestIO()
    # cmd = "READ UR DATA" + "\n"
    cmd = "READ DATA" + "\n"
    cmd.encode('utf-8')
    # cmd = "CURRENT STATE"
    print(str(test.queryServer(cmd)))
    #
    # while True:
    #     print(str(test.queryServer(cmd)))
    #     time.sleep(1)
