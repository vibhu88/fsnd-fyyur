#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import (
Flask, 
render_template, 
request, 
Response, 
flash, 
redirect, 
url_for)
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flasgger import Swagger

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

Swagger (app)

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
  data = []
  venues = Venue.query.all()
  for place in Venue.query.distinct(Venue.city, Venue.state).all():
      data.append({
          'city': place.city,
          'state': place.state,
          'venues': [{
              'id': venue.id,
              'name': venue.name,
          } for venue in venues if
              venue.city == place.city and venue.state == place.state]
      })
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
  """
  This is Fyuur API GET method to fetch information of a particular Venue
  Call this Method passing the venue id within the URI
  ---
  tags:
    - Fyuur API
  parameters:
    - venue_id: venue_id
      in: path
      type: Integer
      required: true
      description: Id of the Venue
  responses:
    Good Response:
      description: Venue Information with Past and Upcoming Shows
    500:
      description: Something went wrong!
  """
  venue=Venue.query.filter(Venue.id == venue_id).first()
  venue_past_shows = []
  venue_upcm_shows = []

  past_shows = Show.query.join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()
  for show in past_shows:
    venue_past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(str(show.start_time))
    })

  upcm_shows = Show.query.join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time >= datetime.now()).all()
  for show in upcm_shows:    
    venue_upcm_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(str(show.start_time))
    })

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
        'website': venue.website,
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
  website        = request.form['website']
  seeking_talent = request.form['seeking_talent']
  seeking_description = request.form['seeking_description']
  st_flag        = True
  try:
  
    if seeking_talent == 'No': 
      st_flag=False 
      seeking_description = None

    venue = Venue(name=name, 
                  city=city, 
                  state=state, 
                  address=address, 
                  phone=phone, 
                  genres=genres,
                  facebook_link=facebook_link,
                  website=website,
                  seeking_talent=st_flag,
                  seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
      db.session.rollback()
      print(f'Error ==> {e}')
      print(sys.exc_info())
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
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occured. Venue ' + venue.name + ' could not be deleted')
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
  """
  This is Fyuur API GET method to fetch information of a particular Artist
  Call this Method passing the artit id within the URI
  ---
  tags:
    - Fyuur API
  parameters:
    - venue_id: artist_id
      in: path
      type: Integer
      required: true
      description: Id of the Artist
  responses:
    Good Response:
      description: Artist Information with Past and Upcoming Shows
    500:
      description: Something went wrong!
  """
  artist=Artist.query.filter(Artist.id == artist_id).first()
  artist_past_shows = []
  artist_upcm_shows = []

  past_shows = Show.query.join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()
  for show in past_shows:
    artist_past_shows.append({
    "venue_id": show.venue_id,
    "venue_name": show.venue.name,
    "venue_image_link": show.venue.image_link,
    "start_time": format_datetime(str(show.start_time))
  })

  upcm_shows = Show.query.join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time >= datetime.now()).all()
  for show in upcm_shows:
    artist_past_shows.append({
    "venue_id": show.venue_id,
    "venue_name": show.venue.name,
    "venue_image_link": show.venue.image_link,
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
        'website': artist.website,
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
      artist.website        = request.form['website']
      artist.seeking_venue  = request.form['seeking_venue']
      artist.seeking_description  = request.form['seeking_description']
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
      db.session.rollback()
      print(sys.exc_info())
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
      venue.website        = request.form['website']
      venue.seeking_venue  = request.form['seeking_talent']
      venue.seeking_description  = request.form['seeking_description']
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
      db.session.rollback()
      print(sys.exc_info())
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
    website        = request.form['website']
    seeking_venue  = request.form['seeking_venue']
    seeking_description = request.form['seeking_description']
    sv_flag        = True
    
    try:
      if seeking_venue == 'No': 
        sv_flag=False 
        seeking_description = None

      artist = Artist(name=name, 
                    city=city, 
                    state=state, 
                    phone=phone, 
                    genres=genres,
                    facebook_link=facebook_link,
                    website=website,
                    seeking_venue=sv_flag,
                    seeking_description=seeking_description)
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

#----------------------------------------------------------------------------#
#  Shows
#----------------------------------------------------------------------------#

@app.route('/shows')
def shows():
  shows=Show.query.join(Artist).join(Venue).all()
  data=[]
  for show in shows:
      sp_show={
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
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
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
    return render_template('pages/home.html')

@app.errorhandler(400)
def bad_request(error):
    return render_template('errors/400.html'), 400

@app.errorhandler(401)
def unauthorized(error):
    return render_template('errors/401.html'), 401

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
