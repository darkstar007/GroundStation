/* -*- c++ -*- */
/* 
 * Copyright 2013 Matthew Nottingham.
 * 
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */


#ifndef INCLUDED_DOPPLER_DOPPLER_C_H
#define INCLUDED_DOPPLER_DOPPLER_C_H

#include <doppler/api.h>
#include <gr_sync_block.h>

namespace gr {
  namespace doppler {

    /*!
     * \brief <+description of block+>
     * \ingroup doppler
     *
     */
    class DOPPLER_API doppler_c : virtual public gr_sync_block
    {
     public:
      typedef boost::shared_ptr<doppler_c> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of doppler::doppler_c.
       *
       * To avoid accidental use of raw pointers, doppler::doppler_c's
       * constructor is in a private implementation
       * class. doppler::doppler_c::make is the public interface for
       * creating new instances.
       */
	 static sptr make(const char *line1, const char *line2, double frequency, double sampling_rate, 
			  double lat, double lon, double alt=0.0, 
			  int year = 0, int month = 0, int day = 0, int hour = 0, int minute = 0, int second = 0, int microsecond = 0);
    };

  } // namespace doppler
} // namespace gr

#endif /* INCLUDED_DOPPLER_DOPPLER_C_H */

