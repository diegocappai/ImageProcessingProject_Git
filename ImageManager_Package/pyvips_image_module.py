#import set_pyvips
import pyvips


class Image:
    def __init__(self, file_path, tile_w, tile_h):
        self.file_path = file_path
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.patches_coords = self.get_coords()

    # Determina la lista di coordinate di tutte le patch
    def get_coords(self,):
        file_path = self.file_path
        tile_h = self.tile_h
        tile_w = self.tile_w

        #Legge solo l'header del file per ottenere le dimensioni
        image = pyvips.Image.new_from_file(file_path)
        x_coords = []
        y_coords = []

        # Determina coordinate per y
        # Gestisce caso tile_h non multiplo di image.height
        if image.height % tile_h != 0:
            num_patches = image.height // tile_h
            used_size = num_patches * tile_h
            started_patch = (image.height - used_size) // 2
            for _ in range(num_patches):
                y_coords.append(started_patch)
                started_patch += tile_h
        else:
            y_coords = list(range(0, image.height, tile_h))

        # Determina coordinate per x
        # Gestisce caso tile_w non multiplo di image.width
        if image.width % tile_w != 0:
            num_patches = image.width // tile_w
            used_size = num_patches * tile_w
            started_patch = (image.width - used_size) // 2
            for _ in range(num_patches):
                x_coords.append(started_patch)
                started_patch += tile_w
        else:
            x_coords = list(range(0, image.width, tile_w))

        patches_coords = [(x, y, tile_w, tile_h) for y in y_coords for x in x_coords]


        return patches_coords


    # Determina le coordinate di una patch specifica
    def find_tile_coords(self, x_coord, y_coord):
        tile_w = self.tile_w
        tile_h = self.tile_h
        patches_coords = self.patches_coords

        tile = next((t for t in patches_coords if t[0]<= x_coord <(t[0]+tile_w) and t[1]<= y_coord <(t[1]+tile_h)))

        if tile:
            return tile
        else:
            print("Coordinata non trovata!")


    # Estrae e salva una singola patch
    def extract_patch(self, output_path, tile_coords):
        file_path = self.file_path

        # Estrae un tassello/patch con le coordinate in input  e la salva su disco.
        # access='random' ottimizza la lettura solo dell'area della patch
        image = pyvips.Image.new_from_file(file_path, access='random')

        # Esegue il ritaglio con le coordinate fornite come argomento
        patch = image.crop(tile_coords[0], tile_coords[1], tile_coords[2], tile_coords[3])

        # Salva patch su disco
        patch.write_to_file(output_path)


# ==========================================
# ESEMPIO D'USO
# ==========================================
if __name__ == "__main__":
    # Inserire percorso immagine e grandezza patch:
    immagine = Image(r"Image/Path", 256, 256)
    output_img = "tile1.png"

    single_tile_coords = immagine.find_tile_coords(12, 698)
    print(single_tile_coords)

    immagine.extract_patch(output_img, single_tile_coords)

    print("Fatto.")