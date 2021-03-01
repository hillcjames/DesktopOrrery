# Orrery as a desktop background

# Using Skyfield
# https://rhodesmill.org/skyfield
# pip install skyfield

import skyfield.api as skyfieldAPI
import math
from PIL import Image, ImageDraw
import sys
import subprocess
from abc import ABCMeta, abstractmethod


# from datetime import timedelta, time

ts = skyfieldAPI.load.timescale()
currentTime = ts.now()

skyfieldPlanets = skyfieldAPI.load('de421.bsp')

class Planet:
    def __init__(self, name, skyfieldData, radiusInKm, color):
        self.name = name
        self.skyfieldData = skyfieldData
        self.radiusInKm = radiusInKm
        self.color = color
        self.positionAu = skyfieldData.at(currentTime).observe(skyfieldPlanets['sun']).position.au

class Style(metaclass=ABCMeta):
    @abstractmethod
    def auDistanceScalingFunction(d):
        return NotImplemented

    @abstractmethod
    def getShadedColor(planet, r, theta, fullRadius):
        return NotImplemented

    @abstractmethod
    def getVisualRadius(planet, imageScale):
        return NotImplemented


class ShadedStyle(Style):
    def auDistanceScalingFunction(d):
        # print("    A    ",d)
        sign = 1 if d > 0 else -1
        return sign * math.pow(abs(d), 0.6)

    def getShadedColor(planet, r, theta, fullRadius):
        alpha = int(155 * math.pow(1 - r/fullRadius, 2))
        return (planet.color + (alpha,))

    def getVisualRadius(planet, imageScale):
        # r = math.sqrt(planetR)/10

        r = math.pow(planet.radiusInKm, 0.4)*3/imageScale
        # r = math.sqrt(planetR)
        if r < 1:
            r = 1
        return r


class TestingStyle(Style):
    def auDistanceScalingFunction(d):
        # print("    A    ",d)
        sign = 1 if d > 0 else -1
        return sign * math.pow(abs(d), 0.6)

    def getShadedColor(planet, r, theta, fullRadius):
        # alpha = 155 * (math.pow(1 - r/fullRadius, 2) * (1.5 + math.sin(11*theta)/4)) // sunburst star
        # alpha = 155 * (math.pow(1 - r/fullRadius, 2) * (0.9 + math.cos(math.sin(11*theta))/4)) // slightly smoother sunburst
        # alpha = 155 * math.pow(1 - r/(fullRadius-2), 2)
        # alpha = 155 * math.cos((1-r/fullRadius) * 2 * math.pi) // ugly simple shpere
        alpha = 0#100 + 50 * math.pow(1 - r/(fullRadius-2), 2)
        # if int(r) >= int(fullRadius*0.7):
        alpha += 50 + 100 * (1 - math.pow(1-r/int(fullRadius*0.5), 8))
        return (planet.color + (int(alpha),))

    def getVisualRadius(planet, imageScale):
        # r = math.sqrt(planetR)/10
         # r = math.sqrt(planetR)
        if r < 1:
            r = 1
        print(planet.name, r)
        return r

class Orrery:
    def __init__(self, resolution):
        self.img = Image.new('RGBA', resolution, (0, 0, 0, 255))
        self.border = 50 # in pixels

        self.style = ShadedStyle
        # self.style = TestingStyle

        self.planets = [
            Planet("Sun", skyfieldPlanets['sun'],                695508,   (200, 180, 0)),
            Planet("Mercury", skyfieldPlanets['MERCURY BARYCENTER'],   2439,   (180, 180, 180)),
            Planet("Venus", skyfieldPlanets['VENUS BARYCENTER'],     6051,   (220, 190, 150)),
            Planet("Earth", skyfieldPlanets['EARTH BARYCENTER'],     6371,   (70, 180, 220)),
            Planet("Moon", skyfieldPlanets['moon'],                 1737,   (150, 150, 150)),
            Planet("Mars", skyfieldPlanets['MARS BARYCENTER'],      3389,   (180, 70, 0)),
            Planet("Jupiter", skyfieldPlanets['JUPITER BARYCENTER'],  69911,   (210, 130, 100)),
            Planet("Saturn", skyfieldPlanets['SATURN BARYCENTER'],   24622,   (200, 180, 70)),
            Planet("Neptune", skyfieldPlanets['NEPTUNE BARYCENTER'],  58232,   (50, 100, 200)),
            Planet("Uranus", skyfieldPlanets['URANUS BARYCENTER'],   24622,   (50, 150, 200)),
            Planet("Pluto", skyfieldPlanets['PLUTO BARYCENTER'],     1188,   (150, 150, 150)) # yea, I know, I know.
        ]
        # self.getImagePositionFromAuPosition([0.001, 0.001])
        # self.getImagePositionFromAuPosition([1, 1])
        # self.getImagePositionFromAuPosition([10, 10])
        # self.getImagePositionFromAuPosition([100, 100])
        # self.getImagePositionFromAuPosition([1000, 1000])

        self.setImageScale()

    def setImageScale(self):
        self.imageScale = 1
        maxR = 0 # radius, in au
        for planet in self.planets:
            # r = math.sqrt(planet.positionAu[0]*planet.positionAu[0] + planet.positionAu[1]*planet.positionAu[1])
            r = max(planet.positionAu[0], planet.positionAu[1])
            # don't need R
            scaledR = self.style.auDistanceScalingFunction(r)
            if scaledR > maxR:
                maxR = scaledR
        self.imageScale = maxR * 2
        print(self.imageScale)

    def start(self):
        # print()
        for planet in self.planets:
            planetImgLayer = self.plotPlanet(planet)
            self.img = Image.alpha_composite(self.img, planetImgLayer)
        self.img.show()
        # self.img.save('abstractOrrrey.png')

    # def plotOrbit(self, planet):

    def plotPlanet(self, planet):
        # time = ts.utc(2020, 5, 13, 10, 32)
        # astrometric = sun.at(currentTime).observe(mars)
        # ra, dec, distance = astrometric.radec()
        # print(ra)
        # print(dec)
        # print(distance)
        # print(planet.skyfieldData.at(currentTime).position.au)
        # print(planet.skyfieldData.at(currentTime).velocity)
        # print(mars.at(currentTime).velocity.au_per_d)

        positionPlanetInImage = self.getImagePositionFromAuPosition(planet.positionAu)
        visualRadius = self.style.getVisualRadius(planet, self.imageScale)

        # self.drawCircle(positionPlanetInImage, visualRadius, planet.color)
        return self.buildImgWithShadedCircle(positionPlanetInImage, visualRadius, planet)


    def getImagePositionFromAuPosition(self, auPosition):

        x = self.scaleDistance(auPosition[0])
        y = self.scaleDistance(auPosition[1])
        print(math.sqrt(x*x + y*y))

        # print(self.imageScale)
        # print(auPosition)
        # print("   ", (x, y))
        return (x, y)

    def scaleDistance(self, d):
        imW, imH =  self.img.size
        imR = (imW if (imW > imH) else imH)/2 - self.border

        scaledD = self.style.auDistanceScalingFunction(d)
        # print("    B    ", scaledD, self.imageScale, imR)
        return (scaledD / self.imageScale) * imR



    # def drawCircle(self, position, r, color=(90, 90, 90)):
    #     # where the origin is the center of the image
    #     imW, imH =  self.img.size
    #     x = imW/2 + position[0] # is z out of the plane, or is y? guess we'll find out
    #     y = imH/2 - position[1]
    #
    #
    #     bbox =  (x - r, y - r, x + r, y + r)
    #     draw = ImageDraw.Draw(self.img)
    #     draw.ellipse(bbox, fill=color)
    #     del draw

    def buildImgWithShadedCircle(self, position, fullRadius, planet):
        # where the origin is the center of the image
        imageLayer = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
        imW, imH =  imageLayer.size
        centerX = imW/2 + position[0]
        centerY = imH/2 - position[1]

        minX = centerX - fullRadius - 1
        minY = centerY - fullRadius - 1
        maxX = centerX + fullRadius + 1
        maxY = centerY + fullRadius + 1
        # draw = ImageDraw.Draw(imageLayer)
        # draw.ellipse(bbox, fill=color)
        print(int(minX), int(maxX), int(minY), int(maxY))
        for i in range(int(minX), int(maxX)):
            for j in range(int(minY), int(maxY)):
                x = i - minX - fullRadius
                y = j - minY - fullRadius
                r = math.sqrt(x*x + y*y)
                # theta = 0
                # if x != 0:
                theta = math.atan2(y,x)
                if r <= fullRadius and x+centerX>=0 and y+centerY>=0 and x+centerX< imW and y+centerY<imH:
                    colorWithShadedAlpha = self.style.getShadedColor(planet, r, theta, fullRadius)
                    imageLayer.putpixel((int(centerX + x), int(centerY + y)), colorWithShadedAlpha)
        # del draw
        return imageLayer

def getResolution():
    resolution = (1920, 1080)
    resoStr = ""
    if len(sys.argv) == 1:
        resoStr = subprocess.check_output(["sh", "getCurrentResolution.sh"]).decode("utf-8").strip()
    else:
         resoStr = sys.argv[1]

    if resoStr != "":
        x, y = resoStr.split("x")[:]
        resolution = (int(x), int(y))
    return resolution

def main():
    resolution = getResolution()
    orrery = Orrery(resolution)
    orrery.start()



if __name__ == "__main__":
    # parse potential args

    main()


# skyfield.eclipselib.lunar_eclipses(start_time, end_time, eph)


# osculating_elements_of(position[, …]) 	Produce the osculating orbital elements for a position.
# OsculatingElements.apoapsis_distance 	Distance object
# OsculatingElements.argument_of_latitude 	Angle object
# OsculatingElements.argument_of_periapsis 	Angle object
# OsculatingElements.eccentric_anomaly 	Angle object
# OsculatingElements.eccentricity 	numpy.ndarray
# OsculatingElements.inclination 	Angle object
# OsculatingElements.longitude_of_ascending_node 	Angle object
# OsculatingElements.longitude_of_periapsis 	Angle object
# OsculatingElements.mean_anomaly 	Angle object
# OsculatingElements.mean_longitude 	Angle object
# OsculatingElements.mean_motion_per_day 	Angle object
# OsculatingElements.periapsis_distance 	Distance object
# OsculatingElements.periapsis_time 	Time object
# OsculatingElements.period_in_days 	numpy.ndarray
# OsculatingElements.semi_latus_rectum 	Distance object
# OsculatingElements.semi_major_axis 	Distance object
# OsculatingElements.semi_minor_axis 	Distance object
# OsculatingElements.time 	Time object
# OsculatingElements.true_anomaly 	Angle object
# OsculatingElements.true_longitude 	Angle object
