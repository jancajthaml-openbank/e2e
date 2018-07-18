require 'net/http'
require 'openssl'
require 'uri'

module RESTServiceHelper

  def get(url)
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)
    http = http.start
    response = nil

    begin
      request = Net::HTTP::Get.new(uri.request_uri)
      request["Accept"] = "application/json;charset=utf8"
      response = http.request(request)
    rescue => error
      case error
      when EOFError, Net::ReadTimeout
        response = Net::HTTPResponse.send(:response_class, "504").new("1.0", "504", "Gateway Timeout")
        response.instance_variable_set(:@body, "{}")
        response.instance_variable_set(:@read, true)
      else
        raise(error)
      end
    end

    return response
  end

  def post(url, data = {})
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)    
    response = nil

    begin
      request = Net::HTTP::Post.new(uri.request_uri)
      request.body = (data.is_a?(Hash) ? data.to_json : data)
      request["Accept"] = "application/json;charset=utf8"
      request["Content-Type"] = "application/json;charset=utf8"
      response = http.request(request)
    rescue => error
      case error
      when EOFError, Net::ReadTimeout
        response = Net::HTTPResponse.send(:response_class, "504").new("1.0", "504", "Gateway Timeout")
        response.instance_variable_set(:@body, "{}")
        response.instance_variable_set(:@read, true)
      else
        raise(error)
      end
    end

    return response
  end

  def patch(url, data = {})
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)
    response = nil

    begin
      request = Net::HTTP::Patch.new(uri.request_uri)
      request.body = (data.is_a?(Hash) ? data.to_json : data)
      request["Accept"] = "application/json;charset=utf8"
      request["Content-Type"] = "application/json;charset=utf8"
      response = http.request(request)
    rescue => error
      case error
      when EOFError, Net::ReadTimeout
        response = Net::HTTPResponse.send(:response_class, "504").new("1.0", "504", "Gateway Timeout")
        response.instance_variable_set(:@body, "{}")
        response.instance_variable_set(:@read, true)
      else
        raise(error)
      end
    end

    return response
  end

  def put(url, data = {})
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)
    response = nil

    begin
      request = Net::HTTP::Put.new(uri.request_uri)
      request.body = (data.is_a?(Hash) ? data.to_json : data)
      request["Accept"] = "application/json;charset=utf8"
      request["Content-Type"] = "application/json;charset=utf8"
      response = http.request(request)
    rescue => error
      case error
      when EOFError, Net::ReadTimeout
        response = Net::HTTPResponse.send(:response_class, "504").new("1.0", "504", "Gateway Timeout")
        response.instance_variable_set(:@body, "{}")
        response.instance_variable_set(:@read, true)
      else
        raise(error)
      end
    end

    return response
  end

  def delete(url)
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)
    response = nil

    begin
      request = Net::HTTP::Delete.new(uri.request_uri)
      request["Accept"] = "application/json;charset=utf8"
      response = http.request(request)
    rescue => error
      case error
      when EOFError, Net::ReadTimeout
        response = Net::HTTPResponse.send(:response_class, "504").new("1.0", "504", "Gateway Timeout")
        response.instance_variable_set(:@body, "{}")
        response.instance_variable_set(:@read, true)
      else
        raise(error)
      end
    end

    return response
  end

  def self.new_client(uri)
    http = Net::HTTP.new(uri.host, uri.port)
    http.read_timeout = 1
    http.open_timeout = 1

    if uri.scheme == "https"
      #puts %x(openssl s_client -showcerts -connect #{uri.host}:https)

      http.use_ssl = true
      http.verify_mode = OpenSSL::SSL::VERIFY_NONE
      http.instance_eval {
        @ssl_context = OpenSSL::SSL::SSLContext.new
        options = OpenSSL::SSL::OP_NO_SSLv2 + OpenSSL::SSL::OP_NO_SSLv3
        options |= OpenSSL::SSL::OP_NO_COMPRESSION if OpenSSL::SSL.const_defined?('OP_NO_COMPRESSION')
        @ssl_context.set_params({ options: options })
        @ssl_context.verify_mode = OpenSSL::SSL::VERIFY_PEER
        @ssl_context.ssl_version = :TLSv1_2
        @ssl_contextciphers = "ALL:!aNULL:!eNULL:!SSLv2"
      }
    else
      http.use_ssl = false
    end

    return http
  end

end
