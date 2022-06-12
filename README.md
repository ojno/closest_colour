Jon French - Prodigi Senior Python Dev Technical Test
=====================================================

Setup and Usage
---------------

```
python3 -m venv venv
source venv/bin/activate , or .\venv\Scripts\Activate.ps1 , or etc
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser (and follow the prompts)
python manage.py runserver

(elsewhere)

curl -u user:pass http://localhost:8000/colours/match?url=http://jonathanfrench.net/test-sample-teal.png
```

See `SAMPLE_RUNS.txt` for some sample JSON output, from manual requests using `curl`.

Django REST Framework also provides a web browser interface to the API; see `SCREENSHOT.png`

Testing
-------

There are tests in the `tests` directory using `pytest`, which can be run with

```
pytest tests
```

Directory Map
-------------

```
.
├── ClosestColour  ...............  Django project package
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py  .............  Django settings file (e.g. colour palette)
│   ├── urls.py
│   └── wsgi.py
├── README.md
├── SAMPLE_RUNS.txt
├── SCREENSHOT.png
├── closest_colour  ..............  Django app package
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── colours.py  ..............  Implementation of nearest neighbour for colours
│   ├── images.py  ...............  Implementation of image representative colour extraction
│   ├── migrations
│   │   ├── __init__.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py  ................  Implementation of REST API endpoint
├── db.sqlite3
├── images  ......................  Test images
│   ├── 1x1black.png
│   ├── 1x1white.png
│   ├── black-square-white-bg.png
│   ├── hsvnoise.png
│   ├── test-sample-black.png
│   ├── test-sample-grey.png
│   ├── test-sample-navy.png
│   └── test-sample-teal.png
├── manage.py
├── pyproject.toml
├── requirements.txt
├── setup.cfg
├── templates
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── test_colours.py  .........  Tests for nearest neighbour for colours
    ├── test_images.py  ..........  Tests for image representative colour extraction
    └── test_view.py  ............  Tests for REST API endpoint
```

The Task
--------

I have implemented this task in Python with Django and Django REST Framework, also using 
NumPy and SciPy for their numeric algorithms.

I broke down the task into three main elements, which I tackled in order: finding the closest
colour to a given target from a given palette; summarising an image into a single representative
(hopefully, background - more on this later) colour; and gluing those two together into an
endpoint which fetches an image from the network and finds its closest colour.

1. Finding the Closest Colour

To find a colour of a given palette which is nearest to a target colour, we are talking about
a nearest neighbour problem in 3D space. (Colours can be thought of as 3D vectors, with the
dimensions being red, green, and blue - or generally, some three values which are related to human
trichromatic vision.) This can be easily solved using *k*-D trees, also known as binary space
partitioning trees. Essentially, the colour space is repeatedly partitioned into segments such
that half of the remaining palette of colours is in each half, until a single colour is reached.
We then have a single nearest neighbour colour, and can calculate the distance from it to the
target and decide if it is within our tolerance. SciPy provides an easy-to-use implementation.

To test this, I needed a sample palette of colours. I chose to use the CSS 3 palette of about
150 colours, which seemed like a realistic amount. The Python `webcolors` package provided this.

Since most images are stored as `RGB` colours, this is the most straightforward space to find
the nearest neighbour in. However, it is not perceptually uniform: because our eyes do not
see all colours equally well, two colours at a given distance in one part of the space, e.g.
two greens, may seem more or less similar to a human observer than e.g. two blues. To combat
this, we can first convert our colours (via a nonlinear transformation) to a space such as the
`Lab` space, which is designed to be perceptually uniform for linear distances. I used the
`colormath` package to convert back and forth between colour spaces, and for its classes used
to represent colours.

However, my experiments with the `Lab` space seemed to give nonintuitive results for the test
images, with `test-sample-teal.png` being given as closest to `darkslategray` rather than `teal`,
which I viewed as being closer. For this reason, I left the default as `RGB` for now.

2. Summarising an Image into One Colour

This part of the task immediately made me think of clustering algorithms. We have an image
with potentially millions of colours in it, and want to find a colour which in some way
'represents' the most common colours in that image. (Assuming I have understood the problem
correctly; see below for considerations around 'background' colours etc.)

To start with, I implemented a very simple naive approach; simply average all the pixels of
an image. This works pretty fast, but has some failure modes. In particular, if you have an
image with *two* popular colours in it, for example some large black shapes on a white background,
the result will be grey, not black or white. This doesn't seem to be what we are looking for,
given the background to the problem.

The next approach I took was a *k*-means clustering algorithm. This is readily available in SciPy,
and lets us find *k* colours which represent averages of popular colours within the image. (See
e.g. Wikipedia https://en.wikipedia.org/wiki/K-means_clustering for more details.) It does run
somewhat slower than the naive approach, but produces much better results. I picked 5, fairly
arbitrarily, as the number of clusters *k*, which seems to work well for most images. Using the
same example, with black shapes on a white background, the image will be separated into black
and white clusters, and then the most popular will be chosen as the representative colour.

3. Putting it All Together

I then implemented a Django Rest Framework API which takes a URL in the query string, fetches
an image from that URL, and applies the two previous results to it. Most of the work here was 
in input and error handling - for example, what happens if an invalid or 404'ing URL is
passed in.


Assumptions and Possible Improvements
-------------------------------------

* I assumed that the palette of available colours changes rarely, and therefore can be declared
statically in code. If this is not the case, and the colours should be defined in a database or
similar, a slight rethink would be needed. For efficiency, it would be best not to rebuild the 
k-D tree structure on every request, so some form of caching and invalidating that cache when
the list of colours is updated would be needed.
* The most 'representative' colour of an image may not be its 'background' colour. It's left
vague in the task description, but if we actually wanted the background colour, i.e. the colour
of the edges, of an image in order to find the correct paper to print it on or something like that, then there are cases where
the system as it is currently might not give the correct colour - one example might be a large black
square almost, but not quite, to the edges of a white background. To fix this, we would need to
add some weighting of pixels in the *k*-means search so pixels towards the edges of an image
are considered more significant.
* Currently, if you request the same image multiple times, the calculation is rerun each time.
It would be possible to cache the result for a given image using a checksum or similar.



Scale
-----

*How would your solution scale to deal with thousands of requests per day?*

There are three phases involved in processing a given image:

1. Fetch the image.

This is IO bound, waiting on a request from the network. Easily scalable.

2. Find the representative colour of the image.

This is CPU bound and is the main bottleneck in the system. As below, I opted to improve its
performance at a slight sacrifice to accuracy by scaling down the image before processing it.
In my testing, this took up to about half a second per image in the worst case using 
the sample data.

3. Find the closest colour to the representative colour from our palette.

While CPU bound, this task is very quick, taking less than 1/100000 of a second per colour 
in my testing. Negligible.

The bottleneck is the finding of a representative colour. Fortunately, this is simply a function
of the input image, not (currently) depending on going to a database or anything like that.
It would therefore be easy to scale this solution horizontally, adding more endpoint nodes behind
a load balancer.

In the problem statement, it's said that the orders don't come in a smooth fashion, instead
bursting around peak times. If the peak times are known, the endpoints could be scaled up in
advance. Otherwise (or possibly as well), some automation could be used such (e.g. AWS Auto Scaling
groups) to scale the system up or down as demand fluctuates. Of course, all of this could be
made irrelevant, or at least made mostly "someone else's problem", by the use of a serverless
platform, below.

Efficiency
----------

I touched on this above already. While it would be great to use the full resolution image for
a colour selection algorithm, with images up to 10000x10000 pixels in size, this is simply not
feasible. I opted to scale down the image (which, even using a high-quality resampler
like Lanczos, is a much faster operation than the *k*-means algorithm I used to find the
representative colour) so the *k*-means algorithm has much less data to work on. 200x200 seemed
like a reasonable compromise which preserves most of the detail in the image, and particularly
the dominant colours, while being fast to process.

Resilience
----------

Given that this endpoint (with the assumptions I have made) is a very standalone system without
any dependencies between requests, I would host this on a 'serverless' platform like AWS Lambda
or Google App Engine. This relieves developers from having to worry about managing servers and
so on, and allows much easier scaling on a pay-as-you-go basis.

There are some very important changes that would need to be made before this could be deployed;
things like setting `DEBUG` to `False` and making settings like `SECRET_KEY` be taken from
e.g. an environment variable or other secret store rather than being stored with the code.

I have implemented a full suite of tests for my solution, with 100% line coverage for all three
parts of the system. This includes unit tests for both the subcomponents of the problem,
as well as end-to-end and regression tests for the entire API.

A system like this which takes in URLs provided by the user and fetches them has several
security considerations that need to be managed. For starters, you don't want users to be able
to misuse your system to implement denial-of-service attacks on other people, by repeatedly
passing their URLs to this system. It is imperative that users are not allowed to use the endpoint
without authenticating, at least not without severe rate-limiting - otherwise some malicious user
would inevitably find the endpoint and use it to DoS someone. In production, I would
implement rate-limiting on a per-user basis if possible. Django REST Framework provides
easy options for doing this with only a few lines of code.

I have used `mypy` for type checking, as well as `black`, `isort` and `flake8` for code style,
to help ensure that the code would be maintainable in the long term.


Alerting and Monitoring
-----------------------

I would use a system such as Sentry or New Relic for alerting and monitoring, along with the 
monitoring tools that most serverless platforms (see above) provide. You could configure it to
alert when requests (or e.g. the 95th percentile of requests, if a few outliers is OK) take
more than a given threshold, say a few seconds, and definitely to alert on any errors 
so they can be investigated.
