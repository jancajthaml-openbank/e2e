require_relative 'rest_service'

class VaultAPI
  include RESTServiceHelper

  attr_reader :base_url

  def initialize()
    @base_url = "http://vault:8080" # fixme discover
  end

  def health_check()
    get("#{base_url}/health")
  end

end
