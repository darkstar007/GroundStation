#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Top Block
# Generated: Sun Jun 30 13:43:27 2013
##################################################

from gnuradio import audio
from gnuradio import blks2
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
from grc_gnuradio import blks2 as grc_blks2
from optparse import OptionParser
import SimpleXMLRPCServer
import threading

class top_block(gr.top_block):

	def __init__(self):
		gr.top_block.__init__(self, "Top Block")

		##################################################
		# Variables
		##################################################
		self.use_pipe = use_pipe = 0
		self.samp_rate = samp_rate = 32000
		self.rec_gain = rec_gain = 50000
		self.pipe_fname = pipe_fname = "/dev/null"
		self.audio_fname = audio_fname = "/dev/null"
		self.af_gain = af_gain = 0.1

		##################################################
		# Blocks
		##################################################
		self.xmlrpc_server_0_0 = SimpleXMLRPCServer.SimpleXMLRPCServer(("localhost", 8091), allow_none=True)
		self.xmlrpc_server_0_0.register_instance(self)
		threading.Thread(target=self.xmlrpc_server_0_0.serve_forever).start()
		self.select1 = grc_blks2.selector(
			item_size=gr.sizeof_short*1,
			num_inputs=1,
			num_outputs=2,
			input_index=0,
			output_index=use_pipe,
		)
		self.gr_throttle_0 = gr.throttle(gr.sizeof_float*1, samp_rate)
		self.gr_null_sink_0 = gr.null_sink(gr.sizeof_short*1)
		self.gr_multiply_const_vxx_1 = gr.multiply_const_vff((af_gain, ))
		self.gr_float_to_short_0 = gr.float_to_short(1, rec_gain)
		self.gr_file_sink_0_0 = gr.file_sink(gr.sizeof_short*1, str(pipe_fname))
		self.gr_file_sink_0_0.set_unbuffered(False)
		self.gr_file_sink_0 = gr.file_sink(gr.sizeof_short*1, str(audio_fname))
		self.gr_file_sink_0.set_unbuffered(False)
		self.blks2_tcp_source_0 = grc_blks2.tcp_source(
			itemsize=gr.sizeof_float*1,
			addr="127.0.0.1",
			port=7892,
			server=False,
		)
		self.blks2_rational_resampler_xxx_1_0_0 = blks2.rational_resampler_fff(
			interpolation=48,
			decimation=32,
			taps=None,
			fractional_bw=None,
		)
		self.blks2_rational_resampler_xxx_1_0 = blks2.rational_resampler_fff(
			interpolation=2205,
			decimation=samp_rate/10,
			taps=None,
			fractional_bw=None,
		)
		self.audio_sink_0 = audio.sink(48000, "pulse", True)

		##################################################
		# Connections
		##################################################
		self.connect((self.gr_multiply_const_vxx_1, 0), (self.audio_sink_0, 0))
		self.connect((self.gr_float_to_short_0, 0), (self.gr_file_sink_0, 0))
		self.connect((self.blks2_rational_resampler_xxx_1_0, 0), (self.gr_float_to_short_0, 0))
		self.connect((self.blks2_tcp_source_0, 0), (self.gr_throttle_0, 0))
		self.connect((self.gr_throttle_0, 0), (self.blks2_rational_resampler_xxx_1_0, 0))
		self.connect((self.blks2_rational_resampler_xxx_1_0_0, 0), (self.gr_multiply_const_vxx_1, 0))
		self.connect((self.gr_throttle_0, 0), (self.blks2_rational_resampler_xxx_1_0_0, 0))
		self.connect((self.select1, 0), (self.gr_null_sink_0, 0))
		self.connect((self.select1, 1), (self.gr_file_sink_0_0, 0))
		self.connect((self.gr_float_to_short_0, 0), (self.select1, 0))


	def get_use_pipe(self):
		return self.use_pipe

	def set_use_pipe(self, use_pipe):
		self.use_pipe = use_pipe
		self.select1.set_output_index(int(self.use_pipe))

	def get_samp_rate(self):
		return self.samp_rate

	def set_samp_rate(self, samp_rate):
		self.samp_rate = samp_rate
		self.gr_throttle_0.set_sample_rate(self.samp_rate)

	def get_rec_gain(self):
		return self.rec_gain

	def set_rec_gain(self, rec_gain):
		self.rec_gain = rec_gain
		self.gr_float_to_short_0.set_scale(self.rec_gain)

	def get_pipe_fname(self):
		return self.pipe_fname

	def set_pipe_fname(self, pipe_fname):
		self.pipe_fname = pipe_fname
		self.gr_file_sink_0_0.open(str(self.pipe_fname))

	def get_audio_fname(self):
		return self.audio_fname

	def set_audio_fname(self, audio_fname):
		self.audio_fname = audio_fname
		self.gr_file_sink_0.open(str(self.audio_fname))

	def get_af_gain(self):
		return self.af_gain

	def set_af_gain(self, af_gain):
		self.af_gain = af_gain
		self.gr_multiply_const_vxx_1.set_k((self.af_gain, ))

if __name__ == '__main__':
	parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
	(options, args) = parser.parse_args()
	tb = top_block()
	tb.run()

