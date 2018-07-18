require_relative 'rest_service'

class RestfulAPI
  include RESTServiceHelper

  def call(http_method, url, data = {})
    m = http_method.downcase
    case m
    when "get", "delete"
      return method(m).call(url)
    when "post", "put", "patch"
      return method(m).call(url, data)
    else
      raise "undefined method #{http_method.upcase}"
    end
  end

end
