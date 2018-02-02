require_relative 'rest_service'

class RestfulAPI
  include RESTServiceHelper

  ######################################################### account methods ####

  def call(http_method, url, data = {})
    case http_method
    when "get";    return get(url)
    when "post";   return post(url, data)
    when "patch";  return patch(url, data)
    when "delete"; return post(url)
    else;          raise "undefined method #{http_method.upcase}"
    end
  end

end
