#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres= db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean())
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', cascade="all, delete-orphan", lazy=True)

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean())
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', cascade="all, delete-orphan", lazy=True)

class Show(db.Model):
    __tablename__ = 'Show'
    
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable = False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable = False)
    start_time = db.Column(db.DateTime, nullable = False )

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#----------------------------------------------------------------------------#
#  Venues
#----------------------------------------------------------------------------#

@app.route('/venues')
def venues():
  all_areas=Venue.query.distinct('city', 'state').all()
  data=[]
  for sp_area in all_areas:
    venue_info=[]
    all_venue_in_sp_area=Venue.query.filter(Venue.city == sp_area.city, Venue.state == sp_area.state).all()
    for sp_venue in all_venue_in_sp_area:
      venue_dict={
        'id': sp_venue.id,
        'name': sp_venue.name,
        'num_upcoming_shows': Show.query.filter(Show.venue_id == sp_venue.id, Show.start_time >= datetime.now()).count()
      }
      venue_info.append(venue_dict)
    venues= {
      'city': sp_area.city,
      'state': sp_area.state,
      'venues': venue_info
    }
    data.append(venues)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  data=[]
  match=0
  search_term = request.form.get('search_term', '')
  venues=Venue.query.all()
  for venue in venues:
    if venue.name.lower().find(search_term.lower()) != -1:
      match=match+1
      match_venue={
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_show': Show.query.filter(Show.venue_id == venue.id, Show.start_time >= datetime.now()).count()
      }
      data.append(match_venue)
  response={
    "count": match,
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue=Venue.query.filter(Venue.id == venue_id).first()
  shows=Show.query.filter(Show.venue_id == venue_id).all()
  venue_past_shows = []
  venue_upcm_shows = []

  for show in shows:
      if show.start_time < datetime.now():
          venue_past_shows.append({
              "artist_id": show.artist_id,
              "artist_name": Artist.query.filter(Artist.id == show.artist_id).first().name,
              "artist_image_link": Artist.query.filter(Artist.id == show.artist_id).first().image_link,
              "start_time": format_datetime(str(show.start_time))
          })
      elif show.start_time >= datetime.now():
          venue_upcm_shows.append({
              "artist_id": show.artist_id,
              "artist_name": Artist.query.filter(Artist.id == show.artist_id).first().name,
              "artist_image_link": Artist.query.filter(Artist.id == show.artist_id).first().image_link,
              "start_time": format_datetime(str(show.start_time))
          })

  # Fields website, image_link, seeking description and seeking talent are only implemented in Model and Controllers
  # And are not implemented in View as they are optional. Hence fetch default values from database.
  data = {
        'id': venue.id,
        'name': venue.name,
        'genres': [],
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'facebook_link': venue.facebook_link,
        'image_link': venue.image_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'past_shows_count': len(venue_past_shows),
        'upcoming_shows_count': len(venue_upcm_shows),
        'past_shows': venue_past_shows,
        'upcoming_shows': venue_upcm_shows
      }
  return render_template('pages/show_venue.html', venue=data)

#  ----------------------------------------------------------------
#  Create Venue                                                   #
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():  
    name           = request.form['name']
    city           = request.form['city']
    state          = request.form['state']
    address        = request.form['address']
    phone          = request.form['phone']
    genres         = request.form.getlist('genres')
    facebook_link  = request.form['facebook_link']
    try:
      venue = Venue(name=name, 
                    city=city, 
                    state=state, 
                    address=address, 
                    phone=phone, 
                    genres=genres,
                    facebook_link=facebook_link)
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # Implemented as a controller and not in view, tested using POSTMAN.
  # Table Venue was updated to have cascade="all, delete-orphan" so that if there are any shows at that venue, those are also deleted
  # Delete was not working without cascade.
  try:
    venue = Venue.query.filter(Venue.id == venue_id).first()
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was deleted!')
  except:
    flash('An error occured. Venue ' + venue.name + ' could not be deleted')
    db.session.rollback()
  finally:
    db.session.close()
    return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data=[]
  all_artists=Artist.query.all()
  for sp_artist in all_artists:
    artist_info={
      'id': sp_artist.id,
      'name': sp_artist.name
    }
    data.append(artist_info)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  data=[]
  match=0
  search_term = request.form.get('search_term', '')
  artists=Artist.query.all()
  for artist in artists:
    if artist.name.lower().find(search_term.lower()) != -1:
      match=match+1
      match_artist={
        'id': artist.id,
        'name': artist.name,
        'num_upcoming_show': Show.query.filter(Show.artist_id == artist.id, Show.start_time >= datetime.now()).count()
      }
      data.append(match_artist)
  response={
    "count": match,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist=Artist.query.filter(Artist.id == artist_id).first()
  shows=Show.query.filter(Show.artist_id == artist_id).all()
  artist_past_shows = []
  artist_upcm_shows = []

  for show in shows:
      if show.start_time < datetime.now():
          artist_past_shows.append({
          "venue_id": show.venue_id,
          "venue_name": Venue.query.filter(Venue.id == show.venue_id).first().name,
          "venue_image_link": Venue.query.filter(Venue.id == show.venue_id).first().image_link,
          "start_time": format_datetime(str(show.start_time))
        })
      elif show.start_time >= datetime.now():
          artist_upcm_shows.append({
          "venue_id": show.venue_id,
          "venue_name": Venue.query.filter(Venue.id == show.venue_id).first().name,
          "venue_image_link": Venue.query.filter(Venue.id == show.venue_id).first().image_link,
          "start_time": format_datetime(str(show.start_time))
        })
  
  # Fields website, image_link, seeking description and seeking venue are only implemented in Model and Controllers
  # And are not implemented in View as they are optional. Hence fetch default values from database.
  data = {
        'id': artist.id,
        'name': artist.name,
        'genres': [],
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        "website": artist.website,
        'facebook_link': artist.facebook_link,
        'image_link': artist.image_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'past_shows_count': len(artist_past_shows),
        'upcoming_shows_count': len(artist_upcm_shows),
        'past_shows': artist_past_shows,
        'upcoming_shows': artist_upcm_shows
      }
  return render_template('pages/show_artist.html', artist=data)

#----------------------------------------------------------------------------#
#  Update
#----------------------------------------------------------------------------#
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  edit_artist = Artist.query.filter(Artist.id == artist_id).first()
  artist={
    "id": edit_artist.id,
    "name": edit_artist.name,
    "genres": edit_artist.genres,
    "city": edit_artist.city,
    "state": edit_artist.state,
    "phone": edit_artist.phone,
    "website": edit_artist.website,
    "facebook_link": edit_artist.facebook_link,
    "seeking_venue": edit_artist.seeking_venue,
    "seeking_description": edit_artist.seeking_description,
    "image_link": edit_artist.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # This is an implementation of artist information edit form. It's optional and hence not been implemented in view.
  # This functionality has been tested with POSTMAN 
    artist = Artist.query.filter(Artist.id == artist_id).first()
    try:
      artist.name           = request.form['name']
      artist.city           = request.form['city']
      artist.state          = request.form['state']
      artist.address        = request.form['address']
      artist.phone          = request.form['phone']
      artist.genres         = request.form.getlist('genres')
      artist.facebook_link  = request.form['facebook_link']
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    finally:
      db.session.close()
      return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  edit_venue = Venue.query.filter(Venue.id == venue_id).first()
  venue={
    "id": edit_venue.id,
    "name": edit_venue.name,
    "genres": edit_venue.genres,
    "city": edit_venue.city,
    "state": edit_venue.state,
    "phone": edit_venue.phone,
    "website": edit_venue.website,
    "facebook_link": edit_venue.facebook_link,
    "seeking_talent": edit_venue.seeking_talent,
    "seeking_description": edit_venue.seeking_description,
    "image_link": edit_venue.image_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # This is an implementation of venue information edit form. It's optional and hence not been implemented in view.
  # This functionality has been tested with POSTMAN 
    venue = Venue.query.filter(Venue.id == venue_id).first()
    try:
      venue.name           = request.form['name']
      venue.city           = request.form['city']
      venue.state          = request.form['state']
      venue.address        = request.form['address']
      venue.phone          = request.form['phone']
      venue.genres         = request.form.getlist('genres')
      venue.facebook_link  = request.form['facebook_link']
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
      db.session.rollback()
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    finally:
      db.session.close()
      return redirect(url_for('show_venue', venue_id=venue_id))

#----------------------------------------------------------------------------#
#  Create Artist
#----------------------------------------------------------------------------#

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    name           = request.form['name']
    city           = request.form['city']
    state          = request.form['state']
    phone          = request.form['phone']
    genres         = request.form.getlist('genres')
    facebook_link  = request.form['facebook_link']
    try:
      artist = Artist(name=name, 
                    city=city, 
                    state=state, 
                    phone=phone, 
                    genres=genres,
                    facebook_link=facebook_link)
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

#----------------------------------------------------------------------------#
#  Shows
#----------------------------------------------------------------------------#

@app.route('/shows')
def shows():
  shows=Show.query.all()
  data=[]
  for show in shows:
      sp_show={
        "venue_id": show.venue_id,
        "venue_name": Venue.query.filter(Venue.id == show.venue_id).first().name,
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter(Artist.id == show.artist_id).first().name,
        "artist_image_link": Artist.query.filter(Artist.id == show.artist_id).first().image_link,
        "start_time": format_datetime(str(show.start_time))
      }
      data.append(sp_show)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  artist_id      = request.form['artist_id']
  venue_id       = request.form['venue_id']
  start_time     = request.form['start_time']
  try:
    show = Show(artist_id=artist_id, 
                venue_id=venue_id, 
                start_time=start_time) 
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
