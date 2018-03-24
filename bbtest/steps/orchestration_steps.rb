require_relative 'placeholders'

step "storage is empty" do
  FileUtils.rm_rf Dir.glob("/data/*")
end

step "container :container_name should be started from scratch" do |container_name|
  prefix = ENV.fetch('COMPOSE_PROJECT_NAME', "")
  containers = %x(docker ps -aqf "name=#{prefix}_#{container_name}" 2>/dev/null)
  expect($?).to be_success

  containers.split("\n").map(&:strip).reject(&:empty?).each { |id|
    eventually(timeout: 3) {
      %x(docker kill --signal="TERM" #{id} >/dev/null 2>&1)
      send ":container running state is :state", id, false
    }
    eventually(timeout: 3) {
      %x(docker start #{id} >/dev/null 2>&1)
      send ":container running state is :state", id, true
    }
  }
end

step "container :container_name should be running" do |container_name|
  prefix = ENV.fetch('COMPOSE_PROJECT_NAME', "")
  containers = %x(docker ps -aqf "name=#{prefix}_#{container_name}" 2>/dev/null)
  expect($?).to be_success

  containers.split("\n").map(&:strip).reject(&:empty?).each { |id|
    eventually(timeout: 3) {
      %x(docker start #{id} >/dev/null 2>&1)
      send ":container running state is :state", id, true
    }
  }
end

step ":host is listening on :port" do |host, port|
  eventually(timeout: 3) {
    %x(nc -z #{host} #{port} 2> /dev/null)
    expect($?).to be_success
  }
end

step ":host is healthy" do |host|
  case host
  when "wall";  $http_client.wall.health_check()
  when "vault"; $http_client.vault.health_check()
  when "lake";  $http_client.lake.health_check()
  else;         raise "unknown host #{host}"
  end
end

step ":container running state is :state" do |container, state|
  eventually(timeout: 3) {
    %x(docker #{state ? "start" : "stop"} #{container} >/dev/null 2>&1)
    container_state = %x(docker inspect -f {{.State.Running}} #{container} 2>/dev/null)
    expect($?).to be_success
    expect(container_state.strip).to eq(state ? "true" : "false")
  }
end
