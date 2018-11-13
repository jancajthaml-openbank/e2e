require 'mongo'

Mongo::Logger.logger.level = Logger::FATAL

module MongoHelper

  def self.start(db)
    begin
      client = Mongo::Client.new([ '127.0.0.1:27017' ], :database => db)
      raise "failed to cleanup account collection" unless client[:account].delete_many.ok?
      raise "failed to cleanup transfer collection" unless client[:transfer].delete_many.ok?
    rescue => _
      raise "Failed to allocate mongo client"
    end

    self.client = client
  end

  def self.stop()
    return if self.client.nil?
    begin
      self.client.close()
    rescue => _
    ensure
      self.client = nil
    end
  end

  def mongo_find(coll, params={})
    MongoHelper.mongo_find(coll, params)
  end

  class << self
    attr_accessor :client
  end

  def self.mongo_find(coll, params={})
    return [] if self.client.nil?
    self.client[coll.to_sym].find(params)
  end

end


