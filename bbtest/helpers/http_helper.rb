require_relative 'wall_api'
require_relative 'search_api'
require_relative 'vault_api'
require_relative 'restful_api'

module HttpClient

  def search
    self.search
  end

  def wall
    self.wall
  end

  def vault
    self.vault
  end

  def any
    self.any
  end

  class << self
    attr_accessor :search,
                  :wall,
                  :vault,
                  :any
  end

  self.search = SearchAPI.new()
  self.wall = WallAPI.new()
  self.vault = VaultAPI.new()
  self.any = RestfulAPI.new()

end
