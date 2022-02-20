from re import search
import dataclasses
from dataclasses import dataclass
import json
import os
import shutil

from cooklang import Recipe
from pelican.settings import DEFAULT_CONFIG
from pelican.urlwrappers import URLWrapper


SOURCE_DIR = 'recipes'
BUILD_DIR = 'content'
IMAGE_DIR = 'content/images'
SEARCH_ENGINE_DATA = 'content/search-data.json'


@dataclass
class SearchEngine:
    documents: list = dataclasses.field(default_factory=list)

    STOP_WORDS = ['på', 'om', 'i', 'med', 'smp', 'og', 'uden']

    @staticmethod
    def tokenize(text: str):
        tokens = [SearchEngine.clean_string(part) for part in text.split(' ')]
        return [t for t in tokens if t and t not in SearchEngine.STOP_WORDS]

    @staticmethod
    def clean_string(text: str):
        return text.lower().strip()

    def add_document(self, document: "Document") -> None:
        self.documents.append(document)

    def serialize(self) -> str:
        return json.dumps([
            dataclasses.asdict(document) for document in self.documents
        ])


@dataclass
class Document:
    url: str
    name: str
    tokens: list[str] = dataclasses.field(default_factory=list)

    def index(self, text: str) -> None:
        self.tokens += SearchEngine.tokenize(text)


def urlify(string: str) -> str:
    """Generate Pelican URL for the given string."""
    # This is a very generous hack, that relies on no special configuration for our setup.
    # It also doesn't use the pelican source precisely as they do, but it works for now.
    wrapper = URLWrapper(string, DEFAULT_CONFIG)
    return f"/{wrapper.slug}.html"


def _purge_directory(directory: str) -> None:
    for dirname, _, filenames in list(os.walk(directory))[::-1]:
        for filename in filenames:
            if not filename.startswith('.'):
                os.remove(os.path.join(dirname, filename))
        if dirname != directory:
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

    search_data = SearchEngine()

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

                document = Document(
                    name=name,
                    url=urlify(name),
                )
                search_data.add_document(document)
                document.index(name)

                if 'tags' in recipe.metadata:
                    metadata['Tags'] = recipe.metadata['tags']
                    document.index(metadata['Tags'])
                metadata['Summary'] = recipe.metadata.get('beskrivelse', name)

                imgpath = src.replace('.cook', '.jpg')
                if os.path.exists(imgpath):
                    imagetarget = target.replace('.md', '.jpg').replace(BUILD_DIR, IMAGE_DIR)
                    _ensure_file_directory(imagetarget)
                    shutil.copyfile(
                        src.replace('.cook', '.jpg'),
                        imagetarget,
                    )
                    metadata['Image'] = imgpath.replace(SOURCE_DIR, '/images')

                if recipe.ingredients:
                    ingr_q = []
                    ingr_woq = []
                    for ingredient in recipe.ingredients:
                        document.index(ingredient.name)
                        if ingredient.quantity:
                            ingr_q.append(
                                f"{ingredient.quantity.amount} "
                                f"{ingredient.quantity.unit or ''}"
                                f" {ingredient.name}"
                            )
                        else:
                            ingr_woq.append(ingredient.name)
                    if ingr_q or ingr_woq:
                        metadata['Ingredients'] = ';'.join(ingr_q + ingr_woq)

                if metadata:
                    fh.write("---\n")
                    for key, value in metadata.items():
                        fh.write(f"{key}: {value}\n")
                    fh.write("---\n")

                # Clean steps for comments
                steps = [s.split('--')[0].strip() for s in recipe.steps]
                steps = [s for s in steps if s]

                for step in steps:
                    fh.write(f"\n{step}\n")

    with open(SEARCH_ENGINE_DATA, 'w+') as fh:
        fh.write(search_data.serialize())


if __name__ == '__main__':
    main()
