require_relative 'placeholders'

step "tenant is :tenant" do |tenant|
  $tenant_id = (tenant == "random" ? (0...8).map { ('A'..'Z').to_a[rand(26)] }.join : tenant)
end

step "storage is empty" do
  FileUtils.rm_rf Dir.glob("/data/*")
end

step "no :container :label is running" do |container, label|

  containers = %x(docker ps -a -f name=#{label} | awk '$2 ~ "#{container}" {print $1}' 2>/dev/null)
  expect($?).to be_success

  ids = containers.split("\n").map(&:strip).reject(&:empty?)

  return if ids.empty?

  ids.each { |id|
    eventually(timeout: 10) {
      puts "wanting to kill #{id}"
      send ":container running state is :state", id, false

      label = %x(docker inspect --format='{{.Name}}' #{id})
      label = ($? == 0 ? label.strip : id)

      if container == "openbank/lake"
        %x(docker exec #{id} journalctl -u lake.service -b | cat >/reports/#{label}.log 2>&1)
      else
        %x(docker logs #{id} >/reports#{label}.log 2>&1)
      end

      %x(docker rm -f #{id} &>/dev/null || :)
    }
  }
end

step ":container running state is :state" do |container, state|
  eventually(timeout: 10) {
    %x(docker #{state ? "start" : "stop"} #{container} >/dev/null 2>&1)
    container_state = %x(docker inspect --format {{.State.Running}} #{container} 2>/dev/null)
    expect($?).to be_success
    expect(container_state.strip).to eq(state ? "true" : "false")
  }
end

step ":container :version is started with" do |container, version, label, params|
  containers = %x(docker ps -a --filter name=#{label} --filter status=running --format "{{.ID}} {{.Image}}")
  expect($?).to be_success
  containers = containers.split("\n").map(&:strip).reject(&:empty?)

  unless containers.empty?
    id, image = containers[0].split(" ")
    return if (image == "#{container}:#{version}")
  end

  send "no :container :label is running", container, label

  prefix = ENV.fetch('COMPOSE_PROJECT_NAME', "")
  my_id = %x(cat /etc/hostname).strip
  simplename = container.split("/")[-1]
  args = [
    "docker",
    "run",
    "-d",
    "--net=#{prefix}_default",
    "--volumes-from=#{my_id}",
    "--log-driver=json-file",
    "-h #{label}",
    "--net-alias=#{label}",
    "--name=#{label}",
    "--privileged"
  ] << params << [
    "#{container}:#{version}",
    "2>&1"
  ]

  id = %x(#{args.join(" ")})
  expect($?).to be_success, id

  eventually(timeout: 15) {
    send ":container running state is :state", id, true
  }

  eventually(timeout: 10) {
    send ":host is healthy", simplename
  }
end

step "search is running" do ||
  send ":container :version is started with", "openbank/search", "master", "search_#{$tenant_id}", [
    "-e SEARCH_LAKE_HOSTNAME=lake",
    "-e SEARCH_MONGO_HOSTNAME=mongodb",
    "-e SEARCH_HTTP_PORT=8080",
    "-e SEARCH_TENANT=#{$tenant_id}",
    "-p 8080"
  ]
end

step "lake is running" do ||
  send ":container :version is started with", "openbank/lake", "master", "lake", [
    "-p 5561",
    "-p 5562",
    "-p 9999"
  ]
end

step "vault is running" do ||
  send ":container :version is started with", "openbank/vault", "master", "vault_#{$tenant_id}", [
    "-e VAULT_STORAGE=/data",
    "-e VAULT_LOG_LEVEL=DEBUG",
    "-e VAULT_HTTP_PORT=8080",
    "-e VAULT_TENANT=#{$tenant_id}",
    "-e VAULT_JOURNAL_SATURATION=100",
    "-e VAULT_SNAPSHOT_SCANINTERVAL=120s",
    "-e VAULT_LAKE_HOSTNAME=lake",
    "-e VAULT_METRICS_REFRESHRATE=1s",
    "-e VAULT_METRICS_OUTPUT=/metrics/e2e_vault_#{$tenant_id}_metrics.json",
    "-v #{ENV["COMPOSE_PROJECT_NAME"]}_journal:/data",
    "-v #{ENV["COMPOSE_PROJECT_NAME"]}_metrics:/metrics",
    "-p 8080"
  ]
end

step "wall is running" do ||
  send ":container :version is started with", "openbank/wall", "master", "wall", [
    "-e WALL_STORAGE=/data",
    "-e WALL_HTTP_PORT=8080",
    "-e WALL_LOG_LEVEL=DEBUG",
    "-e WALL_LAKE_HOSTNAME=lake",
    "-e WALL_METRICS_REFRESHRATE=1s",
    "-e WALL_METRICS_OUTPUT=/metrics/e2e_wall_metrics.json",
    "-v #{ENV["COMPOSE_PROJECT_NAME"]}_journal:/data",
    "-v #{ENV["COMPOSE_PROJECT_NAME"]}_metrics:/metrics",
    "-p 8080"
  ]
end

step "mongo is running" do ||
  send ":container :version is started with", "mongo", "latest", "mongodb", [
    "-e MONGO_DATA_DIR=/data/db",
    "-e MONGO_LOG_DIR=/dev/null",
    "-v #{ENV["COMPOSE_PROJECT_NAME"]}_mongo:/data/db",
    "-p 27017"
  ]
end

step ":host is listening on :port" do |host, port|
  eventually(timeout: 10) {
    %x(nc -z #{host} #{port} 2> /dev/null)
    expect($?).to be_success
  }
end

step ":host is healthy" do |host|
  case host
  when "wall"
    expect(HttpClient.wall.health_check().status).to eq(200)
  when "vault"
    expect(HttpClient.vault.health_check().status).to eq(200)
  when "lake"
    with_deadline(timeout: 1) {
      ZMQHelper.lake_handshake()
    }
  when "search"
    expect(HttpClient.search.health_check().status).to eq(200)
  when "mongo"
    %x(nc -z mongodb 27017 2> /dev/null)
    expect($?).to be_success
  else
    raise "unknown host #{host}"
  end
end
