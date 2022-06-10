from io import IOBase

from colormath.color_objects import sRGBColor
import numpy
from PIL import Image
from scipy.cluster.vq import kmeans2


def open_image(image_file: IOBase) -> numpy.ndarray:
    pil_image = Image.open(image_file)
    # k-means on the full-size image was much too slow (~10s per image on the examples)
    # resize the image to 200x200 using Lanczos, should hopefully
    # preserve enough detail to work with
    resized_image = pil_image.resize((200, 200), resample=Image.LANCZOS)
    numpy_image = numpy.asarray(resized_image)
    return numpy_image / 255.0


# Throughout I am assuming that the input image is in the sRGB colour space which
# of course may not always be true. TODO: support more colour spaces than sRGB.

def image_mean_colour(image: numpy.ndarray) -> sRGBColor:
    mean = image.mean(axis=(0, 1))
    return sRGBColor(*mean)


def image_kmeans_colour(image: numpy.ndarray, clusters=5) -> sRGBColor:
    numpy_colours = image.reshape(-1, image.shape[2])
    centroids, labels = kmeans2(numpy_colours, k=clusters, minit="points")
    counts = numpy.bincount(labels)
    most_popular_centroid = centroids[numpy.argmax(counts)]
    return sRGBColor(*most_popular_centroid)
