from abc import ABC, abstractmethod
from io import IOBase
from typing import Optional, Union

import numpy
from colormath.color_objects import sRGBColor
from PIL import Image
from scipy.cluster.vq import kmeans2

# Throughout I am assuming that the input image is in the sRGB colour space which
# of course may not always be true. TODO: support more colour spaces than sRGB.


# ugly pattern we have to use for typing reasons until PEP 661 lands
class Sentinel:
    pass


SENTINEL = Sentinel()


class ImageColourSummariser(ABC):
    @staticmethod
    def image_file_to_numpy_array(
        image_file: IOBase, resize_to: Union[Optional[int], Sentinel] = SENTINEL
    ) -> numpy.ndarray:
        pil_image = Image.open(image_file)
        # k-means on the full-size image was much too slow (~10s per image on the examples)
        # resize the image to 200x200 (or other supplied size) using Lanczos, should hopefully
        # preserve enough detail to work with while being much faster
        if resize_to is SENTINEL:
            resize_to = 200
        if resize_to is not None:
            resized_image = pil_image.resize((resize_to, resize_to), resample=Image.LANCZOS)
        else:
            resized_image = pil_image
        numpy_image = numpy.asarray(resized_image)
        return numpy_image / 255.0

    @abstractmethod
    def summarise(
        self, image_file: IOBase, resize_to: Union[Optional[int], Sentinel] = SENTINEL
    ) -> sRGBColor:  # pragma: nocover
        pass


class MeanImageColourSummariser(ImageColourSummariser):
    def summarise(self, image_file: IOBase, resize_to: Union[Optional[int], Sentinel] = SENTINEL) -> sRGBColor:
        image = ImageColourSummariser.image_file_to_numpy_array(image_file, resize_to=resize_to)
        mean = image.mean(axis=(0, 1))
        return sRGBColor(*mean)


class KMeansImageColourSummariser(ImageColourSummariser):
    def summarise(
        self, image_file: IOBase, resize_to: Union[Optional[int], Sentinel] = SENTINEL, clusters: int = 5
    ) -> sRGBColor:
        image = ImageColourSummariser.image_file_to_numpy_array(image_file, resize_to=resize_to)
        numpy_colours = image.reshape(-1, image.shape[2])
        centroids, labels = kmeans2(numpy_colours, k=clusters, minit="points")
        counts = numpy.bincount(labels)
        most_popular_centroid = centroids[numpy.argmax(counts)]
        return sRGBColor(*most_popular_centroid)
