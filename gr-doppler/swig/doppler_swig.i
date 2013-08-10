/* -*- c++ -*- */

#define DOPPLER_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "doppler_swig_doc.i"

%{
#include "doppler/doppler_c.h"
%}


%include "doppler/doppler_c.h"
GR_SWIG_BLOCK_MAGIC2(doppler, doppler_c);
