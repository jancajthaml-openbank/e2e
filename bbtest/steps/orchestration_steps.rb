
step "storage is empty" do
  FileUtils.rm_rf Dir.glob("/data/*")
end

step "container :container_name should be started from scratch" do |container_name|
  prefix = ENV.fetch('COMPOSE_PROJECT_NAME', "")
  container_id = %x(docker ps -aqf "name=#{prefix}_#{container_name}" 2>/dev/null)
  expect($?).to be_success

  containers = container_id.split("\n").map(&:strip).reject(&:empty?)
  expect(containers).not_to be_empty

  containers.each { |id|
    %x(docker kill --signal="TERM" #{id} >/dev/null 2>&1)
    expect($?).to be_success
  }

  containers.each { |id|
    %x(docker start #{id} >/dev/null 2>&1)
    expect($?).to be_success
  }

  eventually(timeout: 5) {
    containers.each { |id|
      container_state = %x(docker inspect -f {{.State.Running}} #{id} 2>/dev/null)
      expect($?).to be_success
      expect(container_state.strip).to eq("true")
    }
  }
end

step "container :container_name should be running" do |container_name|
  prefix = ENV.fetch('COMPOSE_PROJECT_NAME', "")
  container_id = %x(docker ps -aqf "name=#{prefix}_#{container_name}" 2>/dev/null)
  expect($?).to be_success

  containers = container_id.split("\n").map(&:strip).reject(&:empty?)
  expect(containers).not_to be_empty

  eventually(timeout: 5) {
    containers.each { |id|
      container_state = %x(docker inspect -f {{.State.Running}} #{id} 2>/dev/null)
      expect($?).to be_success
      expect(container_state.strip).to eq("true")
    }
  }
end

step ":host is listening on :port" do |host, port|
  eventually(timeout: 5) {
    %x(nc -z #{host} #{port} 2> /dev/null)
    expect($?).to be_success
  }
end

step ":host is healthy" do |host|
  case host
  when "wall"; $http_client.wall.health_check()
  else;        raise "unknown host #{host}"
  end
end
