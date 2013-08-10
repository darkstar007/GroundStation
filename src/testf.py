#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Top Block
# Generated: Fri Jul 26 09:17:11 2013
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.gr import firdes
from grc_gnuradio import blks2 as grc_blks2
from grc_gnuradio import wxgui as grc_wxgui
from optparse import OptionParser
import wx

class top_block(grc_wxgui.top_block_gui):

	def __init__(self):
		grc_wxgui.top_block_gui.__init__(self, title="Top Block")
		_icon_path = "/usr/local/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
		self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

		##################################################
		# Variables
		##################################################
		self.samp_rate = samp_rate = 1.536e6

		##################################################
		# Blocks
		##################################################
		self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, "/data/matt/mygnuradio/GroundStation_AubieSat_20130616_20451371411943.dat", True)
		self.blks2_tcp_sink_0 = grc_blks2.tcp_sink(
			itemsize=gr.sizeof_gr_complex*1,
			addr="127.0.0.1",
			port=7840,
			server=True,
		)

		##################################################
		# Connections
		##################################################
		self.connect((self.blocks_file_source_0, 0), (self.blks2_tcp_sink_0, 0))


	def get_samp_rate(self):
		return self.samp_rate

	def set_samp_rate(self, samp_rate):
		self.samp_rate = samp_rate

if __name__ == '__main__':
	parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
	(options, args) = parser.parse_args()
	print '1'
	tb = top_block()
	print '2'
	tb.Run(True)

