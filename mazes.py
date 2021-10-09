#!/usr/bin/env python3

import random

from gif import Gif

def recursive_backtracker_gif(width, height, scale):
    assert width >= 3 and height >= 3

    def get_random_direction(x, y):
        points = []
        if x + 3 < width:  points.append((x + 2, y))
        if x - 2 > 0:      points.append((x - 2, y))
        if y + 3 < height: points.append((x, y + 2))
        if y - 2 > 0:      points.append((x, y - 2))

        points = [(x, y) for x, y in points if cur_maze[x][y]]

        if points:
            return random.choice(points)
        else:
            return None

    def draw_point(x, y, color):
        maze_gif.put_rect(x * scale, y * scale, (x + 1) * scale - 1,
                          (y + 1) * scale - 1, color)

    maze_gif = Gif(width * scale, height * scale, colors)
    cur_maze = [[True for y in range(height)] for x in range(width)]

    maze_gif.next_frame()
    points = [(1, 1)]
    cur_maze[1][1] = False
    draw_point(1, 1, PATH_COLOR)
    maze_gif.next_frame()

    while points:
        x, y = points[-1]
        new_point = get_random_direction(x, y)
        if not new_point:
            points.pop()
            draw_point(x, y, HALL_COLOR)
            if points:
                draw_point((x + points[-1][0]) // 2,
                           (y + points[-1][1]) // 2, HALL_COLOR)
                maze_gif.next_frame(3)
            else:
                maze_gif.next_frame(1000)
        else:
            new_x, new_y = new_point
            cur_maze[new_x][new_y] = False
            draw_point(new_x, new_y, PATH_COLOR)
            cur_maze[(x + new_x) // 2][(y + new_y) // 2] = False
            draw_point((x + new_x) // 2, (y + new_y) // 2, PATH_COLOR)
            points.append(new_point)
            maze_gif.next_frame(5)

    return maze_gif

WALL_COLOR = (0, 0, 0)
PATH_COLOR = (0, 255, 0)
HALL_COLOR = (255, 255, 255)

colors = [WALL_COLOR, PATH_COLOR, HALL_COLOR]

if __name__ == '__main__':
    gif = recursive_backtracker_gif(251, 251, 3)
    gif.write_to_file('maze.gif')
