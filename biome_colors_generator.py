import os
import json
import math
import click
import logging
from zipfile import ZipFile


def search(dp_filepath: str, namespace: str, output: str) -> str:
	'''Iterates through all the custom biomes.'''

	biome_colors = {}
	base_folder = f"{dp_filepath}/data/{namespace}/worldgen/biome"

	def iterate(subdir: str = ""):
		filepath = f"{os.getcwd()}/{base_folder}/{subdir}" if subdir else f"{os.getcwd()}/{base_folder}"

		for item in os.listdir(filepath):

			# Recursive search through directories
			if os.path.isdir(f"{filepath}/{item}"):
				new_subdir = f"{subdir}/{item}" if subdir else item
				iterate(new_subdir)

			# Is a biome json, so generate colors
			elif item.endswith(".json"):
				name = f"{namespace}:{item[:-5]}" if not subdir else f"{namespace}:{subdir}/{item[:-5]}"
				biome_colors[name] = generate(f"{filepath}/{item}")

	iterate()
	return write(biome_colors, dp_filepath, namespace, output)
	

def generate(file: str) -> dict:
	'''Generates colors based on the biome's temeprature and downfall.'''

	with open(file, 'r') as f:
		data = json.load(f)
	
	temp = data["temperature"]
	humid = data["downfall"]

	colors = { "r": 128, "g": 128, "b": 128 }

	rm = (0.5 * (logistic(temp) - logistic(humid))) + 1
	gm = (0.5 * (logistic(temp) + logistic(humid))) + 1
	bm = 2 * (logistic(-1 * (temp - 0.5), -5) - 0.5) + 1

	if (bm > 1 and rm > gm):
		rm, gm = gm, rm
	rm += (2 - rm) * max(0, logistic(temp) - 0.75)
	rm *= max(1, (logistic(-humid) + 0.5))

	multiplier = { "r": rm, "g": gm, "b": bm }

	return {k : v * multiplier[k] for k, v in colors.items()}
	

def logistic(val: float, mult: float = -2.5) -> float:
	'''Uses the Logistic Function to clamp values between 0 and 1.'''

	return 1 / (1 + (math.e ** (mult * val)))
	

def write(biome_colors: dict, dp_filepath: str, namespace: str, output: str) -> str:
	'''Writes the biome_colors.json in the user's preferred output.'''

	filename: str

	match output:
		case "json":
			filename = get_available_filename("biome_colors.json")

			with open(f"{os.getcwd()}/{filename}", 'w') as f:
				json.dump(biome_colors, f, indent=4)

		case "datapack":
			# Init vars and enter dir
			cwd = os.getcwd()
			file_paths = []
			os.chdir(f"{os.getcwd()}/{dp_filepath}")

			# Create the biome_colors
			with open(f"{os.getcwd()}/data/{namespace}/biome_colors.json", 'w') as f:
				json.dump(biome_colors, f, indent=4)

			# Iterate through datapack dir
			for root, dirs, files in os.walk(os.getcwd()):
				for filename in files:
					filepath = os.path.join(root, filename)
					file_paths.append(filepath)

			# Return to CWD and zip it up
			os.chdir(cwd)
			filename = get_available_filename(f"{namespace}_datapack.zip")

			with ZipFile(filename, 'w') as zf:
				for file in file_paths:
					zf.write(file)

	return filename

def get_available_filename(filename: str, count = 0) -> str:
	'''Checks the CWD for the filename so nothing gets overridden.'''

	name, ext = filename.rsplit(".", maxsplit=1)
	checkname = filename if count == 0 else f"{name}_{count}.{ext}"
	
	if os.path.exists(f"{os.getcwd()}/{checkname}"):
		return get_available_filename(checkname, count+1)
	
	return checkname


@click.command()
@click.argument('filepath')
@click.argument('namespace')
@click.option(
	'-o',
	'--output',
	type=click.Choice(["JSON", "DATAPACK"], case_sensitive=False),
	default='JSON',
	help='Whether output should be the `biome_colors.json` file, or the entire datapack containing it. Defaults to only the JSON file.'
)
def color_generator(filepath: str, namespace: str, output: str) -> None:
	'''The CLI for generating jacobsjo's biome_colors.json.'''

	logger = logging.getLogger()
	logger.setLevel('INFO')
	
	# Check if the filepath exists
	if not os.path.isdir(f"{os.getcwd()}/{filepath}"):
		if not os.path.exists(f"{os.getcwd()}/{filepath}"):
			logging.error(f"The filepath `{os.getcwd()}/{filepath}` does not exist.")
		else:
			logging.error(f"The filepath `{os.getcwd()}/{filepath}` is not a directory.")
		exit()

	# Check if the filepath is a datapack
	if not os.path.isfile(f"{os.getcwd()}/{filepath}/pack.mcmeta"):
		logging.error(f"The filepath `{os.getcwd()}/{filepath}` is not a datapack. (There is no pack.mcmeta)")
		exit()

	# Check if the namespace is valid
	if not os.path.isdir(f"{os.getcwd()}/{filepath}/data/{namespace}"):
		logging.error(f"The namespace `{namespace}` does not exist.")
		exit()

	# Check if the namespace has the biome directory
	if not os.path.isdir(f"{os.getcwd()}/{filepath}/data/{namespace}/worldgen/biome"):
		logging.error(f"The `worldgen/biome` directory does not exist in the `{namespace}` namespace.")
		exit()

	# Begin the search and generation of the json file
	filename = search(filepath, namespace, output.lower())
	logging.info(f"Successfully completed - output found at {filename} in the current directory.")


if __name__ == '__main__':
	color_generator()