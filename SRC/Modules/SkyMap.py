# Get time and location
from datetime import datetime
from geopy import Nominatim
from tzwhere import tzwhere
from pytz import timezone, utc

# matplotlib to help display our star map
import matplotlib.pyplot as plt

# skyfield for load datasets and star data
from skyfield.data import hipparcos
from skyfield.api import Star, load, wgs84
from skyfield.projections import build_stereographic_projection

# Libraries to help us create the star map and save it
import shutil
import random
from pathlib import Path
from os.path import exists
from os import getcwd, chdir
from PIL import Image, ImageFont, ImageDraw

# Save logs
import logging


class StarCharts:

    def __init__(self):
        self.root_path = getcwd()
        logging.basicConfig(filename=str(Path(self.root_path + '/Data/Logs/SkyMap.log')),
                            level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(name)s %(message)s'
                            )

    def overlap_images(self, path_sky_map, location, when):
        try:
            font = ImageFont.truetype(str(Path(self.root_path + '/Data/Fonts/OpenSans-Italic.ttf')), 30)

            background = Image.open(str(Path(self.root_path + '/Data/TemplateSkyMap/TemplateSkyMap.png')))
            skymap = Image.open(path_sky_map)
            skymap = skymap.resize((skymap.width // 2, skymap.height // 2))

            new_image = Image.new('RGB', (background.width, background.height))

            position_x = background.width // 2 - skymap.width // 2
            position_y = background.height // 7

            new_image.paste(background, (0, 0))
            new_image.paste(skymap, (position_x, position_y), skymap)

            draw = ImageDraw.Draw(new_image)
            draw.text((background.width // 2 - draw.textsize(str(location), font=font)[0] // 2, background.height - 285), str(location), fill="white", font=font)
            draw.text((background.width // 2 - draw.textsize(str(when), font=font)[0] // 2, background.height - 245), str(when), fill="white", font=font)

            new_image.save(path_sky_map, format='PNG')

            return True

        except Exception as e:
            logging.error(e)
            return False

    async def create(self, location, when, MapModel, User_UID, Map_UID):
        try:
            New_Map = MapModel.create(user_uuid=User_UID, map_uuid=Map_UID)
            ID_Map = New_Map.id

            # Create random name for sky map
            name_sky_map = 'sky_map_' + ''.join([(chr(random.randint(97, 122))) for _ in range(10)]) + '.png'

            when_for_image = when
            location_for_image = location
            save_path = str(Path(self.root_path + '/Media/SkyMaps/' + name_sky_map))

            # Path to skyfield files
            skyfield_files_path = str(Path(self.root_path + '/Data/SkyfieldFiles/'))
            path_de421 = str(Path(self.root_path + '/Data/SkyfieldFiles/de421.bsp'))

            # Change directory to skyfield files and avoid errors with downloading files
            # with permission denied
            current_path = getcwd()
            # Change directory to skyfield files
            chdir(skyfield_files_path)

            # de421 shows position of earth and sun in space
            if exists(path_de421):
                de421 = load(path_de421)
            else:
                de421 = load('de421.bsp')

            # hipparcos dataset contains star location data
            with load.open(hipparcos.URL) as f:
                stars = hipparcos.load_dataframe(f)

            # Return to current directory
            chdir(current_path)

            # Get location coordinates
            locator = Nominatim(user_agent='myGeocoder')
            location = locator.geocode(location)

            # Get latitude and longitude
            lat, long = location.latitude, location.longitude

            # Convert date string into datetime object
            dt = datetime.strptime(when, '%Y-%m-%d %H:%M')

            # Define datetime and convert to utc based on our timezone
            timezone_str = tzwhere.tzwhere().tzNameAt(lat, long)
            local = timezone(timezone_str)

            # Get UTC from local timezone and datetime
            local_dt = local.localize(dt, is_dst=None)
            utc_dt = local_dt.astimezone(utc)

            # Find location of earth and sun and set the observer position
            sun = de421['sun']
            earth = de421['earth']

            # Define observation time from our UTC datetime
            ts = load.timescale()
            t = ts.from_datetime(utc_dt)

            # Define an observer using the world geodetic system data
            observer = wgs84.latlon(latitude_degrees=lat, longitude_degrees=long).at(t)
            position = observer.from_altaz(alt_degrees=90, az_degrees=0)

            ra, dec, distance = observer.radec()
            center_object = Star(ra=ra, dec=dec)

            center = earth.at(t).observe(center_object)
            projection = build_stereographic_projection(center)

            star_positions = earth.at(t).observe(Star.from_dataframe(stars))
            stars['x'], stars['y'] = projection(star_positions)

            # Set chart size
            chart_size = 10
            max_star_size = 100
            limiting_magnitude = 10

            # Select stars that are bright enough to see
            bright_stars = (stars.magnitude <= limiting_magnitude)
            magnitude = stars['magnitude'][bright_stars]

            # Plot stars
            fig, ax = plt.subplots(figsize=(chart_size, chart_size))
            border = plt.Circle((0, 0), 1, color='white', fill=False)

            ax.add_patch(border)

            marker_size = max_star_size * 10 ** (magnitude / -2.5)

            ax.scatter(stars['x'][bright_stars], stars['y'][bright_stars], s=marker_size, color='white', marker='.',
                       linewidths=0, zorder=2)

            horizon = plt.Circle((0, 0), radius=1, transform=ax.transData)

            for col in ax.collections:
                col.set_clip_path(horizon)

            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)
            plt.axis('off')

            plt.savefig(save_path, transparent=True, bbox_inches='tight', dpi=300)

            if self.overlap_images(save_path, location_for_image, when_for_image):
                MapModel.update(url=save_path, status='created').where(MapModel.id == ID_Map).execute()
                return True
            else:
                return False

        except Exception as e:
            logging.error(e)
            return False