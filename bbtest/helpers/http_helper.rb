require_relative 'wall_api'

class HTTPClient

  def wall_service
    @wall_service ||= WallAPI.new()
  end

end
