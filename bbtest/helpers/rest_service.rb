require 'excon'

module RESTServiceHelper

  class << self; attr_accessor :timeout; end

  def get(url)
    Excon.get(url, :read_timeout => RESTServiceHelper.timeout)
  end

  def post(url, data = {})
    headers = {
      'Content-Type' => 'application/json;charset=utf8'
    }
    Excon.post(url, :headers => headers, :body => data.to_json, :read_timeout => RESTServiceHelper.timeout, :write_timeout => RESTServiceHelper.timeout)
  end

  def patch(url, data = {})
    headers = {
      'Content-Type' => 'application/json;charset=utf8'
    }
    Excon.patch(url, :headers => headers, :body => data.to_json, :read_timeout => RESTServiceHelper.timeout, :write_timeout => RESTServiceHelper.timeout)
  end

  def put(url, data = {})
    headers = {
      'Content-Type' => 'application/json;charset=utf8'
    }
    Excon.put(url, :headers => headers, :body => data.to_json, :read_timeout => RESTServiceHelper.timeout, :write_timeout => RESTServiceHelper.timeout)
  end

  def delete(url)
    Excon.delete(url, :headers => headers, :read_timeout => RESTServiceHelper.timeout, :write_timeout => RESTServiceHelper.timeout)
  end

end

RESTServiceHelper.timeout = 2
