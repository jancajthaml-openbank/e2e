require_relative 'wall_api'
require_relative 'vault_api'
require_relative 'lake_api'
require_relative 'restful_api'

class HTTPClient

  def wall
    @wall ||= WallAPI.new()
  end

  def lake
    @lake ||= LakeAPI.new()
  end

  def vault
    @vault ||= VaultAPI.new()
  end

  def any
    @any ||= RestfulAPI.new()
  end

end
