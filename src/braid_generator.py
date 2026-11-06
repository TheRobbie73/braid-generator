from PIL import Image, ImageDraw
from math import sin, cos, pi, atan2

def main():
    image = Image.new('RGB', (160, 160), "white")
    draw = ImageDraw.Draw(image)
    anchors = generate_anchors((80, 80), 76)
    draw_braid(draw, [[0, 2, 1, 3], [1, 0, 3, 2]], [[1, 3, 2, 0]], anchors, ["darkred", "orange", "darkgreen", "darkblue"], ["red", "yellow", "green", "blue"], 8, 3, 1)
    image = image.resize((640, 640), Image.Resampling.NEAREST)
    image.show()

def generate_anchors(centre, radius):
    """Generates the anchors for a hexagon-shaped braid.
    """
    cx, cy = centre
    points = [(cx + radius * cos(i * pi/3 + pi/6), cy + radius * sin(i * pi/3 + pi/6)) for i in range(6)]
    angles = [(i * pi/3 + 5 * pi/6) % (2 * pi) for i in range(6)]
    shifted_points = points[1:] + points[:1]
    result = []
    for prev_point, curr_point, angle in zip(points, shifted_points, angles):
        prev_x, prev_y = prev_point
        curr_x, curr_y = curr_point
        for i in range(8):
            ratio = 0.1 + 0.8 * i / 7
            point_x = prev_x + ratio * (curr_x - prev_x)
            point_y = prev_y + ratio * (curr_y - prev_y)
            result.append((point_x, point_y, angle))
    result.append(result[0])
    return result
        
    
def draw_braid(image_draw, braid, draw_order, anchors, backcolors, forecolors, braid_width, backwidth, forewidth):
    """Draws a braid.

    Args:
        image_draw: the ImageDraw instance used to draw the braid on.
        braid: A list of list of indices. The length of each inner list must be the same and determines the number of threads in the braid. The indices in each inner list must be within 0 (inclusive) to the number of threads (exclusive) and must be unique (e.g. [0, 2, 1] is allowed but [0, 2, 5] or [0, 0, 1] isn't). Indices are concerned with the start of each segment only (i.e. [[2, 1, 0], [2, 1, 0]] will cause the first and third threads to swap twice). The number of inner lists does not need to match the number of segments; It will loop back to the first inner list when it reaches the last inner list.
        draw_order: A list of list of indices, similar format to braid. The order in which threads are drawn in each segment, where indices use the order of the threads at the start of the segment. (e.g. [0, 1, 2] will draw the first thread, then the second, then the third. This puts the first thread at the bottom and the third at the top.) The number of inner lists does not need to match either the number of segments or number of lists in braid; It will also loop back.
        anchors: A list of tuples. Describes the path the braid will take. Tuples are formatted as (x, y, angle), where x and y describes the anchor's position, and angle describes the anchors direction in the range of 0 (inc.) to 2pi (exc.), with 0 pointing right and increasing going clockwise. For a braid that loops back on itself, the first and last anchor must be the same. (This does not guarantee that the same threads will be connected.)
        backcolors: A list of colors. Determines the color of the "back" of each thread. Color can be represented as its name (e.g. "white", check https://github.com/python-pillow/Pillow/blob/main/src/PIL/ImageColor.py#L169 for a list of available names), as its hex (e.g. "#ffffff"), or as RGB (e.g. (255, 255, 255)).
        forecolors: A list of colors. Determines the color of the "front" of each thread. Format the same as backcolors. When a thread is drawn, it is first drawn with the backcolor and backwidth, then that is traced by the frontcolor and frontwidth.
        braid_width: Width of the braid, measured from the centre of the leftmost thread to the centre of the rightmost thread.
        backwidth: Width of the "back" of each thread. If this is bigger than the forewidth, it gives the effect of a border around the thread.
        forewidth: Width of the "front" of each thread.
    """
    num_threads = len(braid[0])
    braid_idx = 0
    draw_order_idx = 0

    def get_points(anchor, num_threads, braid_width):
        anchor_x, anchor_y, angle = anchor
        start_x = anchor_x - braid_width / 2 * sin(angle)
        start_y = anchor_y + braid_width / 2 * cos(angle)
        down_x, down_y = sin(angle), -cos(angle)
        return [(
            start_x + down_x * i/num_threads * braid_width, 
            start_y + down_y * i/num_threads * braid_width
            ) for i in range(num_threads)]

    def get_control_points(point_a, point_b, anchor_a, anchor_b):
        # variables written like a true mathematician
        Ax, Ay, Aa = anchor_a # anchor A position and angle
        Bx, By, Ba = anchor_b # anchor B position and angle
        Cx, Cy = (Ax + Bx) / 2, (Ay + By) / 2
        Ca = midangle(Aa, Ba)
        ax, ay = point_a
        bx, by = point_b
        cax = sin(Ca) * ((ax - Ax) * sin(Aa) - (ay - Ay) * cos(Aa))
        cay = -cos(Ca) * ((ax - Ax) * sin(Aa) - (ay - Ay) * cos(Aa))
        cbx = sin(Ca) * ((bx - Bx) * sin(Ba) - (by - By) * cos(Ba))
        cby = -cos(Ca) * ((bx - Bx) * sin(Ba) - (by - By) * cos(Ba))
        return (Cx + cax, Cy + cay), (Cx + cbx, Cy + cby)

    prev_anchor = anchors[0]
    prev_points = get_points(prev_anchor, num_threads, braid_width)
    for curr_anchor in anchors[1:]:
        curr_points = get_points(curr_anchor, num_threads, braid_width)
        for idx in draw_order[draw_order_idx]:
            prev_point = prev_points[idx]
            curr_point = curr_points[braid[braid_idx][idx]]
            # test
            point_a, point_b = get_control_points(prev_point, curr_point, prev_anchor, curr_anchor)

            draw_bold_bezier(image_draw, prev_point, curr_point, point_a, point_b, backcolors[idx], forecolors[idx], backwidth, forewidth)
        backcolors = [backcolors[idx] for idx in braid[braid_idx]]
        forecolors = [forecolors[idx] for idx in braid[braid_idx]]
        prev_points = curr_points
        prev_anchor = curr_anchor
        braid_idx += 1
        braid_idx %= len(braid)
        draw_order_idx += 1
        draw_order_idx %= len(draw_order)

def draw_bold_bezier(image_draw, start, end, control1, control2, backfill = None, forefill = None, backwidth = 1, forewidth = 1, joint = None):
    draw_cubic_bezier(image_draw, start, end, control1, control2, backfill, backwidth, joint)
    draw_cubic_bezier(image_draw, start, end, control1, control2, forefill, forewidth, joint)
    image_draw.circle(start, forewidth/2, forefill)
    image_draw.circle(end, forewidth/2, forefill)

def draw_cubic_bezier(image_draw, start, end, control1, control2, fill = None, width = 1, joint = None):
    points = [start]
    for i in range(1, 50):
        sx, sy = start
        ex, ey = end
        cx1, cy1 = control1
        cx2, cy2 = control2

        t = i/50
        curr_x = (1 - t)**3 * sx + 3 * (1 - t)**2 * t * cx1 + 3 * (1 - t) * t**2 * cx2 + t**3 * ex
        curr_y = (1 - t)**3 * sy + 3 * (1 - t)**2 * t * cy1 + 3 * (1 - t) * t**2 * cy2 + t**3 * ey
        curr = (curr_x, curr_y)
        points.append(curr)
    points.append(end)
    image_draw.line(points, fill, width, joint)

def midangle(angle_a, angle_b):
    return atan2(sin(angle_a) + sin(angle_b), cos(angle_a) + cos(angle_b))

if __name__ == '__main__':
    main()