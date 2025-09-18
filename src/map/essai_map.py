import pygame
import sys

# ---------------- CONFIG ----------------
# Size of each block (in pixels)
TILE_SIZE = 32


def load_first_frame(path, num_frames=19):
    """
    Load only the first frame from a vertically stacked sprite sheet.

    :param path: Path to the image file
    :param num_frames: How many frames are stacked vertically
    :return: Pygame surface of the first frame
    """
    full_image = pygame.image.load(path).convert_alpha()
    full_width, full_height = full_image.get_size()

    frame_height = full_height // num_frames  # Height of one frame

    # Rectangle for the first frame (x=0, y=0, width=full_width, height=frame_height)
    frame_rect = pygame.Rect(0, 0, full_width, frame_height)

    # Extract that rectangle as a subsurface
    first_frame = full_image.subsurface(frame_rect).copy()

    return first_frame


# Example map (0 = empty, 1 = grass, 2 = stone, etc.)

# map_data = [
#     [4, 4, 4, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
#     [4, 4, 4, 4, 4, 1, 1, 6, 6, 6, 2, 2, 1, 1, 1, 1],
#     [4, 4, 4, 1, 1, 1, 6, 6, 6, 2, 2, 2, 2, 1, 1, 6],
#     [4, 1, 1, 1, 1, 6, 6, 6, 2, 2, 2, 2, 1, 1, 6, 6],
#     [1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 6, 6, 6],
#     [1, 1, 3, 3, 3, 1, 1, 1, 2, 2, 1, 1, 6, 6, 6, 6],
#     [1, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 6, 6, 6],
#     [3, 3, 3, 3, 3, 1, 1, 5, 1, 1, 1, 1, 3, 3, 1, 1],
#     [1, 1, 3, 3, 1, 1, 1, 5, 5, 1, 1, 3, 3, 3, 3, 3],
#     [1, 1, 5, 1, 1, 1, 5, 5, 5, 1, 3, 3, 3, 3, 3, 1],
#     [5, 5, 5, 1, 1, 1, 2, 2, 5, 5, 1, 3, 3, 3, 1, 1],
#     [5, 5, 5, 1, 1, 2, 2, 2, 2, 5, 5, 1, 1, 1, 1, 1],
#     [1, 5, 5, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 4],
#     [1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 4, 4, 4],
#     [1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4],
#     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4, 4]
# ]

map_data = [
    [5, 5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 1, 1, 1, 1, 1, 5, 5, 5, 5, 1, 1, 1, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5],
    [5, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5],
    [1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5, 1, 1, 1, 1, 2, 2, 1, 1, 5, 5, 5],
    [1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 1, 1, 1, 2, 2, 2, 2, 1, 1, 5, 1],
    [3, 3, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 1],
    [3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 5, 5, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1],
    [3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1],
    [3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1],
    [3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1],
    [3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 3],
    [1, 1, 4, 4, 4, 4, 4, 1, 2, 2, 1, 1, 1, 4, 4, 1, 1, 1, 1, 1, 3, 3, 3, 3],
    [1, 4, 4, 4, 4, 4, 1, 2, 2, 2, 2, 1, 4, 4, 4, 4, 1, 1, 3, 3, 3, 3, 3, 3],
    [4, 4, 4, 4, 4, 1, 2, 2, 2, 2, 2, 1, 4, 4, 4, 4, 1, 3, 3, 3, 3, 3, 3, 3],
    [4, 4, 4, 4, 1, 2, 2, 2, 2, 2, 1, 1, 1, 4, 4, 4, 4, 1, 1, 1, 3, 3, 3, 3],
    [1, 4, 4, 1, 2, 2, 2, 2, 2, 1, 1, 1, 1, 4, 4, 4, 4, 4, 1, 1, 1, 1, 3, 3],
    [1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4, 1, 1, 1, 1, 1, 4],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 1, 1, 1, 1, 1, 4, 4, 4],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4, 4, 4, 4],
]

structure_spawn = [
    [7, 0, 0],
    [7, 22, 22],
    [8, 15, 1],
    [8, 12, 5],
    [8, 14, 4],
    [8, 17, 17],
    [8, 14, 13],
    [8, 20, 15],
    [9, 6, 11],
    [9, 1, 12],
    [9, 3, 9],
    [9, 1, 19],
    [9, 4, 21],
]

# Textures for each block type
# ⚠️ Adapt paths to your images (PNG, JPG, etc.)
textures = {
    0: None,  # Empty space → nothing drawn
    1: "../../assets/images/Netherrack.png",
    2: "../../assets/images/Soul_Sand.png",
    3: "../../assets/images/Lava.png",
    4: "../../assets/images/Crimson_Nylium_top.png",
    5: "../../assets/images/Warped_Nylium_top.png",
    6: "../../assets/images/Nether_Gold_Ore.png",
    7: "../../assets/images/bastion.png",
    8: "../../assets/images/Crimson_Fungus.png",
    9: "../../assets/images/Warped_Fungus.png",
}

# ----------------------------------------


def load_textures():
    """Load all textures and resize them to TILE_SIZE."""
    loaded = {}
    for block_id, path in textures.items():
        if path is None:
            loaded[block_id] = None
        else:
            if path == "lava":
                first_block_texture = load_first_frame("images/Lava_long.png")
                first_block_texture = pygame.transform.scale(
                    first_block_texture, (TILE_SIZE, TILE_SIZE)
                )
                loaded[block_id] = first_block_texture
            else:
                if path == "images/bastion.png":
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (TILE_SIZE * 2, TILE_SIZE * 2))
                    loaded[block_id] = img
                else:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    loaded[block_id] = img
    return loaded


def draw_map(screen, map_data, loaded_textures):
    """Draw the entire map based on map_data."""
    for y, row in enumerate(map_data):
        for x, block_id in enumerate(row):
            if loaded_textures[block_id]:
                screen.blit(loaded_textures[block_id], (x * TILE_SIZE, y * TILE_SIZE))

    for structure in structure_spawn:
        if loaded_textures[structure[0]]:
            screen.blit(
                loaded_textures[structure[0]],
                (structure[2] * TILE_SIZE, structure[1] * TILE_SIZE),
            )


def main():
    pygame.init()

    # Window size depends on map size
    width = len(map_data[0]) * TILE_SIZE
    height = len(map_data) * TILE_SIZE
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Map Generator")

    # Load textures
    loaded_textures = load_textures()

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Draw background (black)
        screen.fill((0, 0, 0))

        # Draw map
        draw_map(screen, map_data, loaded_textures)

        # Update display
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
