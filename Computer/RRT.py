import pygame
import math
import random

import time #for time.sleep(x)

pygame.init()

# windows settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Algorytm RRT*')

# colors settings
color_obstacle = (0, 0, 0)
color_unknow_space = (126, 126, 126)
color_free_space = (255, 255, 255)

color_RRT_node_circumference = (0, 0, 0)
color_RRT_node_fill = (255, 0, 0)
color_RRT_branch = (255, 0, 0)
color_RRT_solution = (0, 255, 0)
color_RRT_random_point = (0, 255, 0)

# draw settings
line_thickness = 1
circle_radius = 6
circle_inner_radius = circle_radius * 0.9

# map settings
loaded_map = pygame.image.load("mapa_1.png")
loaded_map = pygame.transform.scale(loaded_map, (SCREEN_WIDTH, SCREEN_HEIGHT))

# classes
class RRT_Node:
    def __init__(self, _position, _parent_index, _cost, _self_index: int):
        self.position = _position
        self.self_index = _self_index
        self.parent_index = _parent_index
        self.radius = 4
        self.inner_radius = self.radius * 0.9
        self.cost = _cost
        self.list_of_neighbors = []

    def show(self):
        pygame.draw.circle(screen, color_RRT_node_circumference, self.position, self.radius)
        # pygame.draw.circle(screen, color_RRT_node_fill, self.position, self.inner_radius)

        font_size = 20
        font = pygame.font.Font(None, font_size)
        text_color = (50, 50, 50)
        # text_to_show = font.render(f"{int(self.self_index)}/{int(self.parent_index)}", True, text_color)
        # text_to_show = font.render(f"{int(self.parent_index)}", True, text_color)
        text_to_show = font.render(f"{int(len(self.list_of_neighbors))}", True, text_color)
        screen.blit(text_to_show, (self.position[0]-7, self.position[1]-20))

# functions
def line_points(start_point, end_point):
    if (start_point == end_point):
        return [start_point]
    
    start_point = [round(start_point[0]), round(start_point[1])]
    end_point   = [round(end_point[0]),   round(end_point[1])]

    dx = abs(end_point[0] - start_point[0])
    dy = abs(end_point[1] - start_point[1])
    # print(str(pygame.mouse.get_pos()) + " " + str(start_point) + " " + str(end_point) + " " + str(dx) + " " + str(dy))

    # draw direction
    if (start_point[0] < end_point[0]):
        stepX = 1
    else:
        stepX = -1

    if (start_point[1] < end_point[1]):
        stepY = 1
    else:
        stepY = -1
    
    list_of_points = []
    point = (start_point[0], start_point[1])

    if (dx > dy): # horizontal
        line_error = (2 * dy) - dx

        for i in range(0, dx):
            list_of_points.append(point)
            point = (point[0] + stepX, point[1])

            if (line_error > 0):
                point = (point[0], point[1] + stepY)
                line_error -=  2 * dx

            line_error += 2 * dy
    else: # vertical
        
        line_error = (2 * dx) - dy

        for i in range(0, dy):
            list_of_points.append(point)
            point = (point[0], point[1] + stepY)

            if (line_error > 0):
                point = (point[0] + stepX, point[1])
                line_error -= 2 * dy
                
            line_error += 2 * dx
    
    return list_of_points

def linear_obstacle_detection(map, start_point, end_point):
    list_of_points = line_points(start_point, end_point)

    for point in list_of_points:        
        if(check_if_point_is_free(map, point) == False):
            return False
    
    return True

def find_nearest_point(list_of_points, goal_point):
    min_distance = float('inf')
    nearest_point = goal_point

    for point_to_check in list_of_points:
        dx = point_to_check[0] - goal_point[0]
        dy = point_to_check[1] - goal_point[1]
        distance = (dx * dx) + (dy * dy)

        if (distance < min_distance):
            min_distance = distance
            nearest_point = point_to_check

    return nearest_point

def find_nearest_node(list_of_nodes, new_dir):
    min_distance = float('inf')
    # nearest_node = new_dir
    
    for node_index, node_to_check in enumerate(list_of_nodes):
        dx = node_to_check.position[0] - new_dir[0]
        dy = node_to_check.position[1] - new_dir[1]

        distance_sq = (dx * dx) + (dy * dy)

        if (distance_sq < min_distance):
            min_distance = distance_sq
            nearest_node = node_to_check
            nearest_node_index = node_index

    min_distance = math.sqrt(min_distance)
    return (nearest_node_index, nearest_node, min_distance)

def find_neighbors(map, list_of_nodes, new_dir, step_max_distance):
    # step_max_distance_sq = step_max_distance * step_max_distance
    # print("MSD: ", step_max_distance_sq)
    list_of_neighbors = []

    # print("LON len", len(list_of_nodes))
    for node_index, node_to_check in enumerate(list_of_nodes):
        dx = node_to_check.position[0] - new_dir[0]
        dy = node_to_check.position[1] - new_dir[1]

        distance = round(math.sqrt((dx * dx) + (dy * dy)), 3)
        # distance_sq = round((dx * dx) + (dy * dy), 3)
        print("NTC: ", node_index, " Dis: ", distance)

        # if(distance_sq > step_max_distance_sq):
        #     continue

        if(distance > step_max_distance):
            continue

        if(distance == 0.0):
            continue

        if(linear_obstacle_detection(map, node_to_check.position, new_dir) == True):
            # distance = math.sqrt(distance_sq)
            list_of_neighbors.append([node_index, distance])

    # print("Num of neighbors: " + str(len(list_of_neighbors)))

    return list_of_neighbors

def find_best_neighbor(list_of_nodes, list_of_neighbors):
    best_cost = float('inf')
    best_neighbor_index = None
    
    print("FBN: ", len(list_of_neighbors))
    for neighbor_to_check in list_of_neighbors:
        node_index = neighbor_to_check[0]
        distance = neighbor_to_check[1]
        node_cost = calculate_full_cost(list_of_nodes, node_index) #+ distance
        print("NC [", node_index, "]: ",  node_cost)

        if(node_cost < best_cost):
            best_cost = node_cost
            best_neighbor_index = node_index
            # print("new best")

    return (best_neighbor_index, distance)

#TODO FIX nakieorwanie sąsiadów na samych siebie
def optimization_of_neighbors(map, list_of_nodes, list_of_neighbors, step_max_distance):
    nodes_to_update = []
    print("\nOpti: ", len(list_of_neighbors))

    for neighbor_to_check in list_of_neighbors:
        neighbor_index = neighbor_to_check[0]
        if(neighbor_index == 0):
            continue

        print("\nNTO: [", neighbor_index, "]")

        neighbor_position = list_of_nodes[neighbor_index].position
        neighbor_sorrounding_nodes = find_neighbors(map, list_of_nodes, neighbor_position, step_max_distance)

        if(len(neighbor_sorrounding_nodes) > 0):
            best_neighbor_index, distance = find_best_neighbor(list_of_nodes, neighbor_sorrounding_nodes)
            nodes_to_update.append([neighbor_index, best_neighbor_index])
    
    return nodes_to_update

def calculate_full_cost(list_of_nodes, start_node_index):
    print("\nCFC [", start_node_index, "]")
    full_cost = list_of_nodes[start_node_index].cost

    next_node_index = list_of_nodes[start_node_index].parent_index
    while(next_node_index >= 0):
        print(full_cost, "NNI: ", next_node_index)
        full_cost += list_of_nodes[next_node_index].cost
        current_node_index = next_node_index
        next_node_index = list_of_nodes[next_node_index].parent_index

        if(next_node_index == current_node_index):
            raise IndexError("Zły numer rodzica")

    print("SN: " + str(start_node_index) + " Cost = " + str(full_cost))
    return full_cost

def goal_check(map, list_of_nodes, step_max_distance, goal_point):
    dx = list_of_nodes[-1].position[0] - goal_point[0]
    dy = list_of_nodes[-1].position[1] - goal_point[1]
    distance = math.sqrt((dx * dx) + (dy * dy))

    if(distance < step_max_distance):
        print("Jest blisko")
        clear_way = linear_obstacle_detection(map, list_of_nodes[-1].position, goal_point)

        if(clear_way == True):
            print("Znaleziono drogę!")
            length = len(list_of_nodes)
            return RRT_Node(goal_point, length-1, distance, length)
        
    return None

def rrt_step(map, list_of_nodes, step_max_distance, goal_point):
    results = goal_check(map, list_of_nodes, step_max_distance, goal_point)

    if(results != None):
        calculate_full_cost(list_of_nodes, len(list_of_nodes)-1)
        global finish 
        finish = True
        return results
    
    clear_way = False
    count = 0

    while(clear_way == False):
        new_direction = random_point(map)
        nearest_node_index, nearest_node, distance = find_nearest_node(list_of_nodes, new_direction)

        if(distance > step_max_distance):
            scale = step_max_distance / distance

            dx = (nearest_node.position[0] - new_direction[0]) * scale
            dy = (nearest_node.position[1] - new_direction[1]) * scale

            new_direction = (nearest_node.position[0] - dx, nearest_node.position[1] - dy)

        clear_way = linear_obstacle_detection(map, nearest_node.position, new_direction)

        # safety
        count += 1
        if(count > 100):
            raise OverflowError("Zbyt duża liczba iteracji, nie znaleziono nowej gałęzi.")

    if(distance > step_max_distance):
        distance = math.sqrt((dx * dx) + (dy * dy))

    new_node = RRT_Node(new_direction, nearest_node_index, distance, len(list_of_nodes))
    return (new_node)

def rrt_star_step(map, list_of_nodes, step_max_distance, goal_point):
    global finish 
    if(finish == False):
        results = goal_check(map, list_of_nodes, step_max_distance, goal_point)

        if(results != None):
            # calculate_full_cost(list_of_nodes, len(list_of_nodes)-1)
            finish = True
            global goal_node
            global goal_node_index
            goal_node = results

            new_list_of_nodes = list_of_nodes + [results]
            goal_node_index = len(list_of_nodes)
            return (results, new_list_of_nodes)

    list_of_neightbors_nodes = []
    count = 0

    while (True):
        new_direction = random_point(map)
        list_of_neightbors_nodes = find_neighbors(map, list_of_nodes, new_direction, step_max_distance)

        if(len(list_of_neightbors_nodes) < 1):

            # safety
            count += 1
            if (count > 100):
                raise OverflowError("Zbyt duża liczba iteracji, nie znaleziono nowej gałęzi.")
            
            continue

        best_neighbor_index, distance = find_best_neighbor(list_of_nodes, list_of_neightbors_nodes)
        # print("count: ", count)
        break

    self_index = len(list_of_nodes)-1
    new_node = RRT_Node(new_direction, best_neighbor_index, distance, self_index)  
    new_list_of_nodes = list_of_nodes + [new_node]

    for node in list_of_neightbors_nodes:
        node_index = node[0]

        # TODO sprawdzac czy sasiad juz nie widnieje przypadkiem na liscie
        new_list_of_nodes[node_index].list_of_neighbors.append(self_index)
        new_list_of_nodes[self_index].list_of_neighbors.append(node_index)

    list_of_nodes_to_update = optimization_of_neighbors(map, new_list_of_nodes, list_of_neightbors_nodes, step_max_distance)

    if(len(list_of_nodes_to_update) > 0):
        for node_to_update in list_of_nodes_to_update:
            node_index = node_to_update[0]
            best_neighbor_index = node_to_update[1]

            #TODO usunąć zapezpieczenie sytuacji której nie powinno być ----------------------------------------------------------------------------------------------
            # if(node_index == best_neighbor_index):
            #     continue






            print("node to update: ", node_index, " new parent: ", best_neighbor_index)
            dx = new_list_of_nodes[node_index].position[0] - new_list_of_nodes[best_neighbor_index].position[0]
            dy = new_list_of_nodes[node_index].position[1] - new_list_of_nodes[best_neighbor_index].position[1]

            distance = math.sqrt((dx * dx) + (dy * dy))
            new_list_of_nodes[node_index].parent_index = best_neighbor_index
            new_list_of_nodes[node_index].cost = distance

    # return (new_node, list_of_nodes)
    return (new_node, new_list_of_nodes)
        
def draw_branches(list_of_nodes):
    for node in list_of_nodes:
        if (node.parent_index >= 0):
            parent_position = list_of_nodes[node.parent_index].position
            pygame.draw.line(screen, color_RRT_branch, node.position, parent_position, line_thickness)

def draw_nodes(list_of_nodes):
    for node in list_of_nodes:
        node.show()

def check_if_point_is_free(map, point):
    point_color = map.get_at((point[0], point[1]))

    if (point_color == color_free_space):
        return True
    
    if (point_color == color_obstacle):
        return False
    
    if (point_color == color_unknow_space):
        return False

    return False

def random_point(map):
    point = (random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
    # point = pygame.mouse.get_pos()

    return point

# main
run = True
finish = False

# point_A = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
point_A = (120, 110)
point_B = (700, 420)
# line = line_points(point_A, point_B)

start_node = RRT_Node(point_A, -1, 0, 0)
goal_node = RRT_Node(point_B, -2, 0, None)
goal_node_index = None
list_of_RRT_nodes = [start_node]
list_of_RRT_nodes_to_update = []
new_node = start_node
# nearest_node_position = point_A

print("Start")
start_time = time.time()
timer_run = True

while run:
    screen.blit(loaded_map, (0, 0))
    # screen.fill(color_unknow_space)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            print("Step!")
            print("----------------------------------------------------------")
            new_node, list_of_RRT_nodes = rrt_star_step(loaded_map, list_of_RRT_nodes, 100, goal_node.position)
            # new_node = rrt_star_step(loaded_map, list_of_RRT_nodes, 100, goal_node.position)
            # list_of_RRT_nodes.append(new_node)



            # new_node = rrt_step(loaded_map, list_of_RRT_nodes, 100, goal_node.position)
            # list_of_RRT_nodes.append(new_node)

            # nearest_node_position = list_of_RRT_nodes[new_node.parent_index].position
           

    draw_branches(list_of_RRT_nodes)
    # pygame.draw.line(screen, color_RRT_branch, (120, 50), (220, 50), line_thickness)

    draw_nodes(list_of_RRT_nodes)
    pygame.draw.circle(screen, color_RRT_node_circumference, new_node.position, circle_radius)
    pygame.draw.circle(screen, color_RRT_random_point, new_node.position, circle_inner_radius)
    pygame.draw.circle(screen, color_RRT_node_circumference, new_node.position, 100, 1)
    pygame.draw.circle(screen, color_RRT_node_circumference, pygame.mouse.get_pos(), 100, 1)

    # goal_node.show()
    pygame.draw.circle(screen, color_RRT_node_circumference, start_node.position, circle_radius)
    pygame.draw.circle(screen, (0, 0, 255), start_node.position, circle_inner_radius)
    pygame.draw.circle(screen, color_RRT_node_circumference, goal_node.position, circle_radius)
    pygame.draw.circle(screen, (0, 255, 255), goal_node.position, circle_inner_radius)

    if(finish == True):
        current_node_index = goal_node_index
        next_node_index = goal_node.parent_index
        while(next_node_index >= 0):
            line_start = list_of_RRT_nodes[current_node_index].position
            line_end = list_of_RRT_nodes[next_node_index].position
            pygame.draw.line(screen, color_RRT_solution, line_start, line_end, line_thickness*2)

            current_node_index = next_node_index
            next_node_index = list_of_RRT_nodes[current_node_index].parent_index
            
    # update pixels
    pygame.display.flip()

    # if(finish != True):
    # if(True != True):
    if(True == True):
        time.sleep(0.25)
        new_node, list_of_RRT_nodes = rrt_star_step(loaded_map, list_of_RRT_nodes, 100, goal_node.position)
        # nearest_node_position = list_of_RRT_nodes[new_node.parent_index].position

        # new_node = rrt_step(loaded_map, list_of_RRT_nodes, 100, goal_node.position)
        # list_of_RRT_nodes.append(new_node)
    else:
        if(timer_run == True):
            print("--- %s seconds ---" % (time.time() - start_time))
            timer_run = False

# while end 
pygame.quit()