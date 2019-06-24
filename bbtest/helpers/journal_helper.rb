module Journal

  def account_latest_snapshot(tenant, account)
    Journal.account_latest_snapshot(tenant, account)
  end

  def account_snapshot(tenant, account, version)
    Journal.account_snapshot(tenant, account, version)
  end

  def transaction(tenant, id)
    Journal.transaction_data(tenant, id)
  end

  def transaction_data(tenant, id)
    Journal.transaction_data(tenant, id)
  end

  def self.transaction_data(tenant, id)
    return nil if id.nil?
    path = "/data/t_#{tenant}/transaction/#{id}"
    raise "transaction #{id} not found" unless File.file?(path)

    File.open(path, 'rb') { |f|
      lines = f.read.split("\n").map(&:strip)
      transfers = lines[1..-1]
      transfers = [] if transfers.nil?

      {
        "id" => id,
        "state" => lines[0],
        "transfers" => transfers.map { |line|
          data = line.split(" ").map(&:strip)

          {
            "id" => data[0],
            "credit" => {
              "tenant" => data[1],
              "name" => data[2],
            },
            "debit" => {
              "tenant" => data[3],
              "name" => data[4],
            },
            "valueDate" => Time.at(data[5].to_i).to_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "amount" => data[6],
            "currency" => data[7],
          }
        }
      }
    }
  end

  def self.account_snapshot(tenant, account, version)
    filename = version.to_s.rjust(10, '0')

    path = "/data/t_#{tenant}/account/#{account}/snapshot/#{filename}"

    File.open(path, 'rb') { |f|
      data = f.read

      lines = data.split("\n").map(&:strip)

      {
        "isBalanceCheck" => lines[0][lines[0].length-1..-1] != "F",
        "format" => lines[0][4...-2],
        "currency" => lines[0][0..2],
        "name" => account,
        "version" => version.to_i,
        "balance" => lines[1],
        "promised" => lines[2],
        "promiseBuffer" => lines[3..-2]
      }
    }
  end

  def self.account_latest_snapshot(tenant, account)
    snapshots = []
    Dir.foreach("/data/t_#{tenant}/account/#{account}/snapshot") { |f|
      snapshots << f unless f.start_with?(".")
    }
    snapshots.sort_by! { |i| -i.to_i }

    return nil if snapshots.empty?
    return self.account_snapshot(tenant, account, snapshots[0])
  end

end
