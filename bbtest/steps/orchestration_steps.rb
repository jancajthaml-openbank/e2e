
step "storage is empty" do
  FileUtils.rm_rf("/data/.", secure: true)
end

step "container :container_name should be running" do |container_name|
  prefix = ENV.fetch('COMPOSE_PROJECT_NAME', "")
  container_id = %x(docker ps -aqf "name=#{prefix}_#{container_name}" 2>/dev/null)
  expect($?).to eq(0), "error running `docker ps -aq`: err:\n #{container_name}"

  eventually(timeout: 5) {
    container_id.split("\n").each { |id|
      container_state = %x(docker inspect -f {{.State.Running}} #{id} 2>/dev/null)
      expect($?).to eq(0), "error running `docker inspect -f {{.State.Running}}`: err:\n #{id}"

      expect(container_state.strip).to eq("true")
    }
  }
end

step "print logs of :container_name" do |container_name|
  prefix = ENV.fetch('COMPOSE_PROJECT_NAME', "")
  container_id = %x(docker ps -aqf "name=#{prefix}_#{container_name}" 2>/dev/null)
  expect($?).to eq(0), "error running `docker ps -aq`: err:\n #{container_name}"

  puts %x(docker logs #{container_id})
end

step "list all containers" do ||
  puts %x(docker ps -a)
end

step ":host is listening on :port" do |host, port|
  eventually(timeout: 5) {
    %x(nc -z #{host} #{port} 2> /dev/null)
    expect($?).to be_success
  }
end

step ":host is healthy" do |host|
  case host
  when "wall"
    $http_client.wall_service.health_check()
  else
    raise "unknown host #{host}"
  end
end
