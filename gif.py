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
        self.width, self.height, self.colors = width, height, colors
        self.color_map = {color: i for i, color in enumerate(colors)}
        self.cur_frame = [[0 for y in range(height)] for x in range(width)]
        self.content = bytes()
        self.write_header()
        self.diff_x1 = 0
        self.diff_y1 = 0
        self.diff_x2 = self.width - 1
        self.diff_y2 = self.height - 1

    def add_diff(self, x, y):
        if self.diff_x1 is None:
            self.diff_x1 = self.diff_x2 = x
            self.diff_y1 = self.diff_y2 = y
        else:
            if x < self.diff_x1:
                self.diff_x1 = x
            elif x > self.diff_x2:
                self.diff_x2 = x
            if y < self.diff_y1:
                self.diff_y1 = y
            elif y > self.diff_y2:
                self.diff_y2 = y

    def put_pixel(self, x, y, color):
        color_val = self.color_map[color]
        if self.cur_frame[x][y] != color_val:
            self.cur_frame[x][y] = self.color_map[color]
            self.add_diff(x, y)

    def put_rect(self, x1, y1, x2, y2, color):
        color_val = self.color_map[color]
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                if self.cur_frame[x][y] != color_val:
                    self.cur_frame[x][y] = color_val
                    self.add_diff(x, y)

    def next_frame(self, delay = 10):
        # No difference between the two frames
        if self.diff_x1 is None:
            return

        # Calculate the width of the region to update
        diff_width = self.diff_x2 - self.diff_x1 + 1
        diff_height = self.diff_y2 - self.diff_y1 + 1

        # Write the first part of the graphic control extension
        self.content += b'\x21\xf9\x04\x00'
        # Write the delay time
        self.content += b'%c%c' % (delay % 256, delay // 256)
        # Write the rest of the graphic control extension
        self.content += b'\x00\x00'
        # Write the image separator
        self.content += b'\x2c'
        # Write the image left and top coordinates
        self.content += b'%c%c' % (self.diff_x1 % 256, self.diff_x1 // 256)
        self.content += b'%c%c' % (self.diff_y1 % 256, self.diff_y1 // 256)
        # Write the image width and height coordinates
        self.content += b'%c%c' % (diff_width % 256, diff_width // 256)
        self.content += b'%c%c' % (diff_height % 256, diff_height // 256)
        # Write byte to specify we don't want a local color table
        self.content += b'\x00'
        # Finally, write the info for the frame
        self.write_frame_difference()

    def write_frame_difference(self):
        min_code_size = math.ceil(math.log2(len(self.colors)))
        code_length = min_code_size + 1
        clear_code = 2 ** min_code_size
        end_code = clear_code + 1

        self.content += bytes([min_code_size])
        bits = BitString()

        index_buffer = tuple()
        code_table = {(i,): i for i in range(clear_code)}
        next_code = end_code + 1
        for x in range(self.diff_x1, self.diff_x2 + 1):
            for y in range(self.diff_y1, self.diff_y2 + 1):
                val = self.cur_frame[x][y]
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

        self.content += bits.get_bytes()
        self.content += b'\x00'
        self.diff_x1 = self.diff_y1 = self.diff_x2 = self.diff_y2 = None

    def write_header(self):
        # Some values used in the gif header
        color_res = math.ceil(math.log2(len(self.colors))) - 1
        logical_screen = 1 << 7 | color_res << 4 | color_res

        # Write the GIF version string
        self.content += b'GIF89a'
        # Write the canvas width and height
        self.content += b'%c%c' % (self.width % 256, self.width // 256)
        self.content += b'%c%c' % (self.height % 256, self.height // 256)
        # Write tbe packed field
        self.content += b'%c' % logical_screen
        # Write some outdated useless garbage required by the GIF standard
        self.content += b'\x00\x00'
        # Write the color table
        for i in range(1 << color_res + 1):
            if i < len(self.colors):
                self.content += bytes(self.colors[i])
            else:
                # If we ran out of colors, but the color table still needs
                # to be filled out, we just write black repeatedly
                self.content += b'\x00\x00\x00'
        # Write the application extension to allow animation
        self.content += b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00'

    def write_to_file(self, filename):
        with open(filename, 'wb') as file:
            file.write(self.content)
            # Write ending byte
            file.write(b'\x3b')
