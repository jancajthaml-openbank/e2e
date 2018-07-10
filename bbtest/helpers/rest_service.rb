require 'net/http'
require 'openssl'
require 'uri'

module RESTServiceHelper

  class << self; attr_accessor :timeout; end

  def get(url, no_timeout = true)
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)

    begin
      request = Net::HTTP::Get.new(uri.request_uri)
      request["Accept"] = "application/json;charset=utf8"
      http.request(request)
    rescue => error
      case error
      when Net::ReadTimeout
        if no_timeout
          retry
        else
          raise(error)
        end
      else
        raise(error)
      end
    end
  end

  def post(url, data = {}, no_timeout = true)
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)
    request = Net::HTTP::Post.new(uri.request_uri)
    request.body = (data.is_a?(Hash) ? data.to_json : data)
    request["Accept"] = "application/json;charset=utf8"
    request["Content-Type"] = "application/json;charset=utf8"

    begin
      http.request(request)
    rescue => error
      case error
      when Net::ReadTimeout
        if no_timeout
          retry
        else
          raise(error)
        end
      else
        raise(error)
      end
    end
  end

  def patch(url, data = {}, no_timeout = true)
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)
    request = Net::HTTP::Patch.new(uri.request_uri)
    request.body = (data.is_a?(Hash) ? data.to_json : data)
    request["Accept"] = "application/json;charset=utf8"
    request["Content-Type"] = "application/json;charset=utf8"

    begin
      http.request(request)
    rescue => error
      case error
      when Net::ReadTimeout
        if no_timeout
          retry
        else
          raise(error)
        end
      else
        raise(error)
      end
    end
  end

  def put(url, data = {}, no_timeout = true)
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)
    request = Net::HTTP::Put.new(uri.request_uri)
    request.body = (data.is_a?(Hash) ? data.to_json : data)
    request["Accept"] = "application/json;charset=utf8"
    request["Content-Type"] = "application/json;charset=utf8"

    begin
      http.request(request)
    rescue => error
      case error
      when Net::ReadTimeout
        if no_timeout
          retry
        else
          raise(error)
        end
      else
        raise(error)
      end
    end
  end

  def delete(url, no_timeout = true)
    uri = URI(url)
    http = RESTServiceHelper.new_client(uri)
    request = Net::HTTP::Delete.new(uri.request_uri)
    request["Accept"] = "application/json;charset=utf8"

    begin
      http.request(request)
    rescue => error
      case error
      when Net::ReadTimeout
        if no_timeout
          retry
        else
          raise(error)
        end
      else
        raise(error)
      end
    end

  end

  def self.new_client(uri)
    http = Net::HTTP.new(uri.host, uri.port)
    http.read_timeout = 2
    http.open_timeout = 2

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
    end

    return http
  end

end
