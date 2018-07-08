require 'ffi-rzmq'
require 'thread'

module ZMQHelper

  def self.start
    raise "cannot start when shutting down" if self.poisonPill
    self.poisonPill = false

    begin
      ctx = ZMQ::Context.new
      pull_channel = ctx.socket(ZMQ::SUB)
      pull_channel.setsockopt(ZMQ::SUBSCRIBE, '')
      raise "unable to bind SUB" unless pull_channel.connect("tcp://lake:5561") >= 0
      pub_channel = ctx.socket(ZMQ::PUSH)
      raise "unable to bind PUSH" unless pub_channel.connect("tcp://lake:5562") >= 0
    rescue ContextError => _
      raise "Failed to allocate context or socket!"
    end

    self.ctx = ctx
    self.pull_channel = pull_channel
    self.pub_channel = pub_channel

    self.ready = false
  end

  def self.stop
    self.poisonPill = true
    begin
      self.pull_daemon.join() unless self.pull_daemon.nil?
      self.pub_channel.close() unless self.pub_channel.nil?
      self.pull_channel.close() unless self.pull_channel.nil?
      self.ctx.terminate() unless self.ctx.nil?
      self.ctx = nil
      self.pub_channel = nil
      self.pull_channel = nil
    ensure
      self.pull_daemon = nil
    end
    self.poisonPill = false
  end

  def lake_handshake
    ZMQHelper.lake_handshake()
  end

  class << self
    attr_accessor :ctx,
                  :pull_channel,
                  :pub_channel,
                  :pull_daemon,
                  :poisonPill,
                  :ready,
                  :ping
  end

  self.poisonPill = false
  self.ping = "!"

  def self.lake_handshake()
    # rubocop:disable PerceivedComplexity

    self.ping = "!" + (0...8).map { (65 + rand(26)).chr }.join

    self.pull_daemon = Thread.new do
      loop do
        break if self.poisonPill or self.pull_channel.nil?
        data = ""
        self.pull_channel.recv_string(data, ZMQ::DONTWAIT)
        next if data.empty?
        if data == self.ping and !self.ready
          self.ready = true
          self.poisonPill = true
        end
      end
      self.pull_channel.setsockopt(ZMQ::UNSUBSCRIBE, '') unless self.pull_channel.nil?
      self.pull_channel.close() unless self.pull_channel.nil?
      self.pull_channel = nil
    end

    until self.ready
      self.pub_channel.send_string(self.ping)
      sleep(0.1)
    end

    self.pull_daemon.join() unless self.pull_daemon.nil?

    # rubocop:enable PerceivedComplexity
  end

end
