#!/usr/bin/env python
# 
# Copyright 2013 Matthew Nottingham.
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

from gnuradio import gr, gr_unittest
import doppler_swig as doppler

class qa_doppler_c (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        # set up fg
        sample_rate = 256000
        source = gr.sig_source_c(sample_rate, gr.GR_COS_WAVE, 0.0, 1, 0)

        d = doppler.doppler_c('1 35935U 09051E   13214.30935178  .00000351  00000-0  95268-4 0  2690',
                              '2 35935  98.3696 322.5545 0007075 281.7840  78.2562 14.53379957204541',
                              437.0e6, sample_rate,
                              52.44332,-0.10982,10.0,
                              2013, 8, 3, 13, 39, 0, 0)
        
        self.tb.run ()
        # check data


if __name__ == '__main__':
    gr_unittest.run(qa_doppler_c, "qa_doppler_c.xml")
