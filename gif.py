import math

class BitString:
    def __init__(self):
        self.bits = bytearray()
        self.num_bits = 0

    def add_bits(self, num, width):
        string = bin(num)[2:].zfill(width)
        for digit in reversed(string):
            if len(self.bits) * 8 == self.num_bits:
                self.bits.append(0)
            if digit == '1':
                self.bits[-1] |= 1 << self.num_bits % 8
            self.num_bits += 1

    def get_bytes(self):
        encoded_bytes = bytearray()
        while len(self.bits) > 255:
            encoded_bytes += bytearray([255]) + self.bits[:255]
            self.bits = self.bits[255:]
        if len(self.bits) > 0:
            encoded_bytes += bytearray([len(self.bits)]) + self.bits
        return encoded_bytes

class Gif:
    def __init__(self, width, height, colors):
        self.width = width
        self.height = height
        self.colors = colors
        self.color_map = {color: i for i, color in enumerate(colors)}
        self.pixels = [[0 for y in range(height)] for x in range(width)]
        self.frames = []

    def put_pixel(self, x, y, color):
        self.pixels[x][y] = self.color_map[color]

    def put_rect(self, x1, y1, x2, y2, color):
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                self.pixels[x][y] = self.color_map[color]

    def next_frame(self, delay=10):
        if self.frames and self.frames[-1][0] == self.pixels:
            # If there's no difference between the last frame and
            # this one, just add a longer delay to the current frame
            self.frames[-1][1] += delay
        else:
            self.frames.append([self.pixels, delay])
            self.pixels = [[self.pixels[x][y]
                            for y in range(self.height)]
                            for x in range(self.width)]

    def write_header(self, file):
        # Some values used in the gif header
        color_res = math.ceil(math.log2(len(self.colors))) - 1
        logical_screen = 1 << 7 | color_res << 4 | color_res

        # Write the GIF version string
        file.write(b'GIF89a')
        # Write the canvas width and height
        file.write(b'%c%c' % (self.width % 256, self.width // 256))
        file.write(b'%c%c' % (self.height % 256, self.height // 256))
        # Write tbe packed field
        file.write(b'%c' % logical_screen)
        # Write some outdated useless garbage required by the GIF standard
        file.write(b'\x00\x00')
        # Write the color table
        for i in range(1 << color_res + 1):
            if i < len(self.colors):
                file.write(bytes(self.colors[i]))
            else:
                # If we ran out of colors, but the color table still needs
                # to be filled out, we just write black repeatedly
                file.write(b'\x00\x00\x00')
        # Write the application extension to allow animation
        file.write(b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00')

    def write_frame(self, file, new_frame, prev_frame=None):
        if prev_frame is None:
            diff_x1, diff_x2 = 0, self.width - 1
            diff_y1, diff_y2 = 0, self.height - 1
        else:
            # Get the corners of where the frames differ
            diff_x1, diff_x2, diff_y1, diff_y2 = (None,) * 4
            for x in range(self.width):
                for y in range(self.height):
                    if new_frame[0][x][y] != prev_frame[0][x][y]:
                        if diff_x1 is None:
                            diff_x1 = x
                        diff_x2 = x
                        if diff_y1 is None or diff_y1 > y:
                            diff_y1 = y
                        if diff_y2 is None or diff_y2 < y:
                            diff_y2 = y
        # Calculate the width of the differing rectangle
        diff_width = diff_x2 - diff_x1 + 1
        diff_height = diff_y2 - diff_y1 + 1

        # Write the first part of the graphic control extension
        file.write(b'\x21\xf9\x04\x00')
        # Write the delay time
        file.write(b'%c%c' % (new_frame[1] % 256, new_frame[1] // 256))
        # Write the rest of the graphic control extension
        file.write(b'\x00\x00')
        # Write the image separator
        file.write(b'\x2c')
        # Write the image left and top coordinates
        file.write(b'%c%c' % (diff_x1 % 256, diff_x1 // 256))
        file.write(b'%c%c' % (diff_y1 % 256, diff_y1 // 256))
        # Write the image width and height coordinates
        file.write(b'%c%c' % (diff_width % 256, diff_width // 256))
        file.write(b'%c%c' % (diff_height % 256, diff_height // 256))
        # Write byte to specify we don't want a local color table
        file.write(b'\x00')
        # Finally, write the info for the frame
        self.write_frame_region(file, new_frame[0], diff_x1, diff_y1, diff_x2, diff_y2)

    def write_frame_region(self, file, frame, x1, y1, x2, y2):
        min_code_size = math.ceil(math.log2(len(self.colors)))
        code_length = min_code_size + 1
        clear_code = 2 ** min_code_size
        end_code = clear_code + 1

        file.write(bytes([min_code_size]))
        bits = BitString()

        index_buffer = tuple()
        code_table = {(i,): i for i in range(clear_code)}
        next_code = end_code + 1
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                val = frame[x][y]
                index_buffer += (val,)
                if index_buffer not in code_table:
                    code_table[index_buffer] = next_code
                    bits.add_bits(code_table[index_buffer[:-1]], code_length)
                    index_buffer = (val,)
                    next_code += 1
                    if next_code == 2 ** code_length + 1:
                        code_length += 1
        bits.add_bits(code_table[index_buffer], code_length)
        bits.add_bits(end_code, code_length)

        file.write(bits.get_bytes())
        file.write(b'\x00')

    def write_frames(self, file):
        prev_frame = None
        for frame in self.frames:
            self.write_frame(file, frame, prev_frame)
            prev_frame = frame

    def write(self, filename):
        with open(filename, 'wb') as file:
            self.write_header(file)
            self.write_frames(file)
            # Trailing byte, indicates the end of the file
            file.write(b'\x3b')
