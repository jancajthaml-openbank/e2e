require_relative 'eventually_helper'
require_relative 'mongo_helper'

require 'timeout'
require 'thread'

Thread.abort_on_exception = true

Encoding.default_external = Encoding::UTF_8
Encoding.default_internal = Encoding::UTF_8

class ApplianceHelper

  attr_reader :units

  def download_artifacts()
    %x(mkdir -p /opt/artifacts)
    [
      "lake",
      "vault",
      "wall",
      "search"
    ].map { |service|
      Thread.new do
        begin
          %x(docker pull openbank/#{service}:master)
        rescue ThreadError
        end
      end
    }.map(&:join)

    [
      "lake",
      "vault",
      "wall",
      "search"
    ].map { |service|
      Thread.new do
        begin
          %x(docker run --name temp-container-#{service} openbank/#{service}:master /bin/true)
          %x(docker cp temp-container-#{service}:/opt/artifacts /opt/artifacts/#{service})
          %x(docker rm temp-container-#{service})
        rescue ThreadError
        end
      end
    }.map(&:join)
  end

  def install_packages()
    [
      "lake/lake_*_amd64.deb",
      "vault/vault_*_amd64.deb",
      "wall/wall_*_amd64.deb",
      "search/search_*.deb",
    ].each { |service|
      id, wildcard = service.split("/")
      %x(find /opt/artifacts/#{id} -type f -name '#{wildcard}')
      .split("\n")
      .map(&:strip)
      .reject { |x| x.empty? }
      .each { |package|
        %x(apt-get -y install -qq -o=Dpkg::Use-Pty=0 -f #{package})
      }
    }
  end

  def start()
    units = %x(systemctl -t service --no-legend | awk '{ print $1 }' | sort -t @ -k 2 -g)

    @units = units.split("\n").map(&:strip).reject { |x|
      x.empty? || !(
        x.start_with?("vault") ||
        x.start_with?("lake")  ||
        x.start_with?("wall")  ||
        x.start_with?("search")
      )
    }.map { |x| x.chomp(".service") }

    MongoHelper.start("graphql")

    @units.each { |unit|
      %x(systemctl start #{unit})
    } unless @units.nil?
  end

  def cleanup()
  end

  def ready?()
    actual = %x(systemctl -t service --no-legend | awk '{ print $1 }' | sort -t @ -k 2 -g)
    raise false unless $? == 0

    actual = actual.split("\n").map(&:strip).reject { |x|
      x.empty? || !(
        x.start_with?("vault") ||
        x.start_with?("lake")  ||
        x.start_with?("wall")  ||
        x.start_with?("search")
      )
    }.map { |x| x.chomp(".service") }

    return @units.all? { |e| actual.include?(e) }
  end

  def update_units()
    units = %x(systemctl -t service --no-legend | awk '{ print $1 }' | sort -t @ -k 2 -g)
    raise false unless $? == 0

    @units = units.split("\n").map(&:strip).reject { |x|
      x.empty? || !(
        x.start_with?("vault") ||
        x.start_with?("lake")  ||
        x.start_with?("wall")  ||
        x.start_with?("search")
      )
    }.map { |x| x.chomp(".service") }
  end

  def get_wall_instances()
    units=%x(systemctl -t service --no-legend | awk '{ print $1 }' | grep wall@)

    raise [] unless $? == 0

    return units.split("\n").map(&:strip).reject { |x|
      x.empty? || !x.start_with?("wall@")
    }.map { |x| x.chomp(".service") }
  end

  def get_metrics(unit)
    if unit.include?("@")
      metrics_file = "/opt/#{unit[/[^@]+/]}/metrics/metrics.#{unit[/([^@]+)$/]}.json"
    else
      metrics_file = "/opt/#{unit}/metrics/metrics.json"
    end

    return {} unless File.file?(metrics_file)
    return File.open(metrics_file, 'rb') { |f| JSON.parse(f.read) }
  end

  def teardown()
    return if @units.nil?

    @units.each { |unit|
      %x(systemctl stop #{unit})
      %x(journalctl -o short-precise -u #{unit} --no-pager > /reports/logs/#{unit.gsub('@','_')}.log 2>&1)

      if unit.include?("@")
        metrics_file = "/opt/#{unit[/[^@]+/]}/metrics/metrics.#{unit[/([^@]+)$/]}.json"
      else
        metrics_file = "/opt/#{unit}/metrics/metrics.json"
      end

      File.open(metrics_file, 'rb') { |fr|
        File.open("/reports/metrics/#{unit.gsub('@','_')}.json", 'w') { |fw|
          fw.write(fr.read)
        }
      } if File.file?(metrics_file)
    }

    MongoHelper.stop()
  end

end
