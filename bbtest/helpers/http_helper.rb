require_relative 'server_service_api'

class HTTPClient

  def server_service
    @server_service ||= ServerServiceAPI.new()
  end

end
