import os
import shutil

from cooklang import Recipe


SOURCE_DIR = 'src'
BUILD_DIR = 'pelican/content'
IMAGE_DIR = 'pelican/content'


def _purge_directory(directory: str) -> None:
    for dirname, _, filenames in list(os.walk(directory))[::-1]:
        for filename in filenames:
            os.remove(os.path.join(dirname, filename))
        os.rmdir(dirname)


def _ensure_directory(directory: str) -> None:
    if not os.path.exists(directory):
        os.makedirs(directory)


def _ensure_file_directory(filename: str) -> None:
    _ensure_directory(os.path.dirname(filename))


def clean_build():
    _purge_directory(BUILD_DIR)
    _purge_directory(IMAGE_DIR)


def main():
    clean_build()

    for dirname, _, filenames in os.walk(SOURCE_DIR):
        for filename in filenames:

            if not filename.endswith('.cook'):
                continue

            src = os.path.join(dirname, filename)

            with open(src, 'r') as fh:
                recipe = Recipe.parse(fh.read())

            target = os.path.join(
                BUILD_DIR,
                dirname[len(SOURCE_DIR)+1:],
                filename.replace('.cook', '.md'))

            _ensure_file_directory(target)

            with open(target, 'w+') as fh:
                metadata = {
                    'Category': dirname[len(SOURCE_DIR)+1:]
                }

                name = filename.replace('.cook', '').replace('-', ' ')
                if 'name' in recipe.metadata:
                    name = recipe.metadata.pop('name')
                metadata['Title'] = name

                if 'tags' in recipe.metadata:
                    metadata['Tags'] = recipe.metadata['tags']
                metadata['Summary'] = recipe.metadata.get('beskrivelse', name)

                imgpath = src.replace('.cook', '.jpg')
                if os.path.exists(imgpath):
                    imagetarget = target.replace('.md', '.jpg').replace(BUILD_DIR, IMAGE_DIR)
                    _ensure_file_directory(imagetarget)
                    shutil.copyfile(
                        src.replace('.cook', '.jpg'),
                        imagetarget,
                    )
                    metadata['Image'] = os.path.basename(imgpath)

                if metadata:
                    fh.write("---\n")
                    for key, value in metadata.items():
                        fh.write(f"{key}: {value}\n")
                    fh.write("---\n")

                #for key, value in recipe.metadata.items():
                #    fh.write(f"\n{key.capitalize()}: **{value}**\n")
                if 'Image' in metadata:
                    fh.write(f"\n![Photo]({{attach}}{metadata['Image']})\n")
                if recipe.ingredients:
                    fh.write("\n### Ingredienser\n")
                    for ingredient in recipe.ingredients:
                        if ingredient.quantity:
                            fh.write(
                                f" * {ingredient.quantity.amount} "
                                f"{ingredient.quantity.unit or ''}"
                                f" {ingredient.name}\n"
                            )
                        else:
                            fh.write(f" * {ingredient.name}\n")

                # Clean steps for comments
                steps = [s.split('--')[0].strip() for s in recipe.steps]
                steps = [s for s in steps if s]

                if steps:
                    fh.write("""\n### Opskrift\n""")
                    for step in steps:
                        fh.write(f"\n{step}\n")


# TODO: cooklang bugs
#  * kommentarer bliver ikke håndteret - heller ikke block comments
#  * URLs ser ud til at blive truncated
#  * tider bliver ikke håndteret
#  * udstyr bliver ikke håndteret

if __name__ == '__main__':
    main()
