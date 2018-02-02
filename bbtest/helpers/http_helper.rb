require_relative 'wall_api'
require_relative 'restful_api'

class HTTPClient

  def wall
    @wall ||= WallAPI.new()
  end

  def any
    @any ||= RestfulAPI.new()
  end

end
