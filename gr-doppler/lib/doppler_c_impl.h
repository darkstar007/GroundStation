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

#ifndef INCLUDED_DOPPLER_DOPPLER_C_IMPL_H
#define INCLUDED_DOPPLER_DOPPLER_C_IMPL_H

#include <doppler/doppler_c.h>

#include <SGP4/CoordTopocentric.h>
#include <SGP4/CoordGeodetic.h>
#include <SGP4/Observer.h>
#include <SGP4/SGP4.h>


namespace gr {
  namespace doppler {

    class doppler_c_impl : public doppler_c
    {
     private:
	 Observer * obs;
	 Tle * tle;
	 SGP4 * sgp4;
	 DateTime * now;
	 double sampling_rate;
	 double frequency;
	 double phs;

     public:
	 doppler_c_impl(const char *line1, const char *line2, double frequency, double sampling_freq, 
			double lat, double lon, double alt, 
			int year, int month, int day, int hour, int minute, int second, int microsecond);
      ~doppler_c_impl();

      // Where all the action really happens
      int work(int noutput_items,
	       gr_vector_const_void_star &input_items,
	       gr_vector_void_star &output_items);
    };

  } // namespace doppler
} // namespace gr

#endif /* INCLUDED_DOPPLER_DOPPLER_C_IMPL_H */

