require_relative 'placeholders'

step "tenant is :tenant" do |tenant|
  $tenant_id = (tenant == "random" ? (0...8).map { ('A'..'Z').to_a[rand(26)] }.join : tenant)
end

step "storage is empty" do
  FileUtils.rm_rf Dir.glob("/data/*")
end

step "no :container :label is running" do |container, label|

  containers = %x(docker ps -a -f name=#{label} | awk '{ print $1,$2 }' | grep #{container} | awk '{print $1 }' 2>/dev/null)
  expect($?).to be_success

  ids = containers.split("\n").map(&:strip).reject(&:empty?)

  return if ids.empty?

  ids.each { |id|
    eventually(timeout: 3) {
      puts "wanting to kill #{id}"
      send ":container running state is :state", id, false

      label = %x(docker inspect --format='{{.Name}}' #{id})
      label = ($? == 0 ? label.strip : id)

      %x(docker logs #{id} >/reports#{label}.log 2>&1)
      %x(docker rm -f #{id} &>/dev/null || :)
    }
  }
end

step ":container running state is :state" do |container, state|
  eventually(timeout: 5) {
    %x(docker #{state ? "start" : "stop"} #{container} >/dev/null 2>&1)
    container_state = %x(docker inspect -f {{.State.Running}} #{container} 2>/dev/null)
    expect($?).to be_success
    expect(container_state.strip).to eq(state ? "true" : "false")
  }
end

step ":container :version is started with" do |container, version, label, params|
  containers = %x(docker ps -a -f status=running -f name=#{label} | awk '{ print $1,$2 }' | sed 1,1d)
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
    "--name=#{label}"
  ] << params << [
    "#{container}:#{version}",
    "2>&1"
  ]

  id = %x(#{args.join(" ")})
  expect($?).to be_success, id

  eventually(timeout: 3) {
    send ":container running state is :state", id, true
  }

  eventually(timeout: 3) {
    send ":host is healthy", simplename
  }
end

step "reporting is running" do ||
  send ":container :version is started with", "openbank/reporting", "master", "reporting_#{$tenant_id}", [
    "-e REPORTING_LAKE_HOSTNAME=lake",
    "-e REPORTING_MONGO_HOSTNAME=mongodb",
    "-e REPORTING_HTTP_PORT=8080",
    "-e REPORTING_TENANT=#{$tenant_id}",
    "-p 8080"
  ]
end

step "lake is running" do ||
  send ":container :version is started with", "openbank/lake", "master", "lake", [
    "-e LAKE_LOG_LEVEL=DEBUG",
    "-e LAKE_HTTP_PORT=8080",
    "-p 5561",
    "-p 5562",
    "-p 8080"
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
  eventually(timeout: 3) {
    %x(nc -z #{host} #{port} 2> /dev/null)
    expect($?).to be_success
  }
end

step ":host is healthy" do |host|
  case host
  when "wall"
    resp = $http_client.wall.health_check()
    expect(resp.status).to eq(200)
  when "vault"
    resp = $http_client.vault.health_check()
    expect(resp.status).to eq(200)
  when "lake"
    resp = $http_client.lake.health_check()
    expect(resp.status).to eq(200)
  when "mongo"
    %x(nc -z mongodb 27017 2> /dev/null)
    expect($?).to be_success
  when "reporting"
    $http_client.reporting.health_check()
    expect($?).to be_success
  else
    raise "unknown host #{host}"
  end
end
