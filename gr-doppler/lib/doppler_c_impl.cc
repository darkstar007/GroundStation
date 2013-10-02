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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "doppler_c_impl.h"

namespace gr {
  namespace doppler {

    doppler_c::sptr
    doppler_c::make(const char *line1, const char *line2, double frequency, double sampling_freq, 
		    double lat, double lon, double alt, 
		    int year, int month, int day, int hour, int minute, int second, int microsecond)
    {
      return gnuradio::get_initial_sptr
	   (new doppler_c_impl(line1, line2, frequency, sampling_freq, lat, lon, alt, 
			       year, month, day, hour, minute, second, microsecond));
    }

    /*
     * The private constructor
     */
       doppler_c_impl::doppler_c_impl(const char *line1, const char *line2, double frequency, double sampling_freq, 
				      double lat, double lon, double alt, 
				      int year, int month, int day, int hour, int minute, int second, int microsecond)
	    : gr::sync_block("doppler_c",
		      gr::io_signature::make(0, 0, 0),
		      gr::io_signature::make(1, 1, sizeof(gr_complex)))
    {
	 this->obs = new Observer(lat, lon, alt);
	 this->tle = new Tle("My sat              ", line1, line2);
	 this->now = new DateTime();
	 this->now->Initialise(year, month, day, hour, minute, second, microsecond);
	 this->sampling_rate = sampling_freq;
	 this->frequency = frequency;
	 this->phs = 0.0;
	 this->sgp4 = new SGP4(*tle);

	 std::cout << this->frequency << std::endl << *tle << std::endl;
    }

    /*
     * Our virtual destructor.
     */
    doppler_c_impl::~doppler_c_impl()
    {
    }

    int
    doppler_c_impl::work(int noutput_items,
			  gr_vector_const_void_star &input_items,
			  gr_vector_void_star &output_items)
    {
	 //const <+ITYPE+> *in = (const <+ITYPE+> *) input_items[0];
        gr_complex *out = (gr_complex *) output_items[0];
	double dfrequency;
	double rr;
	//std::cout << *now << std::endl << ((double)noutput_items / sampling_rate) << std::endl;
        // Do <+signal processing+>
	Eci eci1 = sgp4->FindPosition(*now);
	CoordTopocentric topo1 = obs->GetLookAngle(eci1);

	*now = now->AddSeconds((double)noutput_items / sampling_rate);
	//std::cout << *now << std::endl << std::endl;
	Eci eci2 = sgp4->FindPosition(*now);
	CoordTopocentric topo2 = obs->GetLookAngle(eci2);

	for (int i = 0; i < noutput_items; i++) {
	     rr = (topo1.range_rate + ((topo2.range_rate - topo1.range_rate) * ((double) i / (double) noutput_items))) * 1000.0;
	     dfrequency = frequency * rr / 3e8;
	     phs += dfrequency * 2.0 * M_PI / sampling_rate;
	     out[i] = gr_complex(cos(phs), sin(phs));
	     
	}
	phs = fmod(phs, 2 * M_PI);
        // Tell runtime system how many output items we produced.
        return noutput_items;
    }

  } /* namespace doppler */
} /* namespace gr */

