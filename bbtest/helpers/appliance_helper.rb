require_relative 'eventually_helper'

require 'timeout'

Encoding.default_external = Encoding::UTF_8
Encoding.default_internal = Encoding::UTF_8

class ApplianceHelper

  attr_reader :units

  def start()
    units = %x(systemctl -t service --no-legend | awk '{ print $1 }' | sort -t @ -k 2 -g)

    @units = units.split("\n").map(&:strip).reject { |x|
      x.empty? || !(x.start_with?("vault") || x.start_with?("lake") || x.start_with?("wall"))
    }.map { |x| x.chomp(".service") }
  end

  def ready?()
    actual = %x(systemctl -t service --no-legend | awk '{ print $1 }' | sort -t @ -k 2 -g)
    raise false unless $? == 0

    actual = actual.split("\n").map(&:strip).reject { |x|
      x.empty? || !(x.start_with?("vault") || x.start_with?("lake") || x.start_with?("wall"))
    }.map { |x| x.chomp(".service") }

    return @units.all? { |e| actual.include?(e) }
  end

  def onboard_vault(tenant)
    out = %x(systemctl enable vault@#{tenant} 2>&1)
    raise "failed to enable unit with error: #{out}" unless $? == 0

    out = %x(systemctl start vault@#{tenant} 2>&1)
    raise "failed to start unit with error: #{out}" unless $? == 0

    @units << "vault@#{tenant}"

    EventuallyHelper.eventually(timeout: 2) {
      out = %x(systemctl show -p SubState "vault@#{tenant}" 2>&1 | sed 's/SubState=//g')
      raise "expected vault@#{tenant} to be running is #{out}" unless out.strip == "running"
    }
  end

  def get_wall_instances()
    units=%x(systemctl -t service --no-legend | awk '{ print $1 }' | grep wall@)

    raise [] unless $? == 0

    return units.split("\n").map(&:strip).reject { |x|
      x.empty? || !x.start_with?("wall@")
    }.map { |x| x.chomp(".service") }
  end

  def get_metrics(unit)
    if unit.include? "@"
      metrics_file = "/opt/#{unit[/[^@]+/]}/metrics/metrics.json.#{unit[/([^@]+)$/]}"
    else
      metrics_file = "/opt/#{unit}/metrics/metrics.json"
    end

    return nil unless File.file?(metrics_file)
    return File.open(metrics_file, 'rb') { |f| JSON.parse(f.read) }
  end

  def teardown()
    return if @units.nil?

    @units.each { |unit|
      %x(systemctl stop #{unit})
      %x(journalctl -o short-precise -u #{unit} --no-pager > /reports/logs/#{unit.gsub('@','_')}.log 2>&1)

      if unit.include? "@"
        metrics_file = "/opt/#{unit[/[^@]+/]}/metrics/metrics.json.#{unit[/([^@]+)$/]}"
      else
        metrics_file = "/opt/#{unit}/metrics/metrics.json"
      end

      File.open(metrics_file, 'rb') { |fr|
        File.open("/reports/metrics/#{unit.gsub('@','_')}.json", 'w') { |fw|
          fw.write(fr.read)
        }
      } if File.file?(metrics_file)
    }
  end

end
