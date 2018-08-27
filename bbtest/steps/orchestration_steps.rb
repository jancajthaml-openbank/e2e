#require_relative 'placeholders'
#
#
## fixme rename cointaer to image
#step "no :container :label is running" do |container, label|
  #containers = %x(docker ps -a -f name=#{label} | awk '$2 ~ "#{container}" {print $1}' 2>/dev/null)
  #expect($?).to be_success
#
  #ids = containers.split("\n").map(&:strip).reject(&:empty?)
#
  #return if ids.empty?
#
  #ids.each { |id|
    #eventually(timeout: 10) {
      #send ":container running state is :state", id, false
#
      #label = %x(docker inspect --format='{{.Name}}' #{id})
      #label = ($? == 0 ? label.strip : id)
#
      #if container == "openbank/lake"
        #%x(docker exec #{id} journalctl -u lake.service -b | cat > /logs/#{label}.log 2>&1)
      #else
        #%x(docker logs #{id} > /logs/#{label}.log 2>&1)
      #end
#
      #%x(docker rm -f #{id} &>/dev/null || :)
    #}
  #}
#end
#
#step ":container running state is :state" do |container, state|
  #eventually(timeout: 10) {
    #%x(docker #{state ? "start" : "stop"} #{container} >/dev/null 2>&1)
    #container_state = %x(docker inspect --format {{.State.Running}} #{container} 2>/dev/null)
    #expect($?).to be_success
    #expect(container_state.strip).to eq(state ? "true" : "false")
  #}
#end
#
#step ":container :version is started with" do |container, version, label, params|
  #containers = %x(docker ps -a --filter name=#{label} --filter status=running --format "{{.ID}} {{.Image}}")
  #expect($?).to be_success
  #containers = containers.split("\n").map(&:strip).reject(&:empty?)
#
  #unless containers.empty?
    #id, image = containers[0].split(" ")
    #return if (image == "#{container}:#{version}")
  #end
#
  #send "no :container :label is running", container, label
#
  #prefix = ENV.fetch('COMPOSE_PROJECT_NAME', "")
  #my_id = %x(cat /etc/hostname).strip
  #simplename = container.split("/")[-1]
  #args = [
    #"/usr/bin/docker", "run", "-d",
    #"-h", label,
    #"--net=#{prefix}_default",
    #"--volumes-from=#{my_id}",
    #"--log-driver=json-file",
    #"--net-alias=#{label}",
    #"--name=#{label}",
    #"--privileged"
  #] << params << [
    #"#{container}:#{version}",
    #"2>&1"
  #]
#
  #id = %x(#{args.join(" ")})
  #expect($?).to be_success, id
#
  #eventually(timeout: 15) {
    #send ":container running state is :state", id, true
  #}
#
  #eventually(timeout: 10) {
    #expect(HttpClient.search.health_check().code.to_i).to eq(200)
  #}
#end
#
#step "search is running" do ||
  #send ":container :version is started with", "openbank/search", "master", "search_#{$tenant_id}", [
    #"-e SEARCH_LAKE_HOSTNAME=lake",
    #"-e SEARCH_MONGO_HOSTNAME=mongodb",
    #"-e SEARCH_LOG_LEVEL=DEBUG",
    #"-e SEARCH_HTTP_PORT=8080",
    #"-e SEARCH_TENANT=#{$tenant_id}",
    #"-p 8080"
  #]
#end
#
#step "mongo is running" do ||
  #send ":container :version is started with", "mongo", "latest", "mongodb", [
    #"-e MONGO_DATA_DIR=/data/db",
    #"-e MONGO_LOG_DIR=/dev/null",
    #"-v #{ENV["COMPOSE_PROJECT_NAME"]}_mongo:/data/db",
    #"-p 27017"
  #]
#end
#
