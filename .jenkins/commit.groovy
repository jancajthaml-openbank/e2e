def artifactory = Artifactory.server "artifactory"

pipeline {

    agent {
        label 'docker'
    }

    options {
        skipDefaultCheckout(true)
        ansiColor('xterm')
        buildDiscarder(logRotator(numToKeepStr: '10', artifactNumToKeepStr: '10'))
        disableConcurrentBuilds()
        disableResume()
        timeout(time: 10, unit: 'MINUTES')
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                script {
                    currentBuild.displayName = "#${currentBuild.number} - ?"
                }
                deleteDir()
                checkout(scm)
            }
        }

        stage('Setup') {
            steps {
                script {
                    env.GIT_BRANCH = sh(
                        script: 'git name-rev --name-only HEAD',
                        returnStdout: true
                    ).trim() - 'remotes/origin/'
                    env.ARCH = sh(
                        script: 'dpkg --print-architecture',
                        returnStdout: true
                    ).trim()

                    currentBuild.displayName = "#${currentBuild.number} - ${env.GIT_BRANCH}"
                }
            }
        }

        stage('Download') {
            steps {
                script {
                    artifactory.download spec: """{
                        "files": [
                            {
                                "flat": true,
                                "pattern": "generic-local/openbank/lake/1.3.2/linux/amd64/lake.deb",
                                "target": "${env.WORKSPACE}/tmp/lake_1.3.2_amd64.deb"
                            },
                            {
                                "flat": true,
                                "pattern": "generic-local/openbank/vault/1.3.5/linux/amd64/vault.deb",
                                "target": "${env.WORKSPACE}/tmp/vault_1.3.5_amd64.deb"
                            },
                            {
                                "flat": true,
                                "pattern": "generic-local/openbank/ledger/1.1.4/linux/amd64/ledger.deb",
                                "target": "${env.WORKSPACE}/tmp/ledger_1.1.4_amd64.deb"
                            },
                            {
                                "flat": true,
                                "pattern": "generic-local/openbank/data-warehouse/1.1.1/linux/amd64/data-warehouse.deb",
                                "target": "${env.WORKSPACE}/tmp/data-warehouse_1.1.1_amd64.deb"
                            },
                            {
                                "flat": true,
                                "pattern": "generic-local/openbank/postgres/1.0.0/linux/amd64/postgres.deb",
                                "target": "${env.WORKSPACE}/tmp/postgres_1.0.0_amd64.deb"
                            }
                        ]
                    }"""

                    echo sh(
                        script: 'ls -la tmp',
                        returnStdout: true
                    ).trim()

                }
            }
        }

        stage('BlackBox Test') {
            agent {
                docker {
                    image "jancajthaml/bbtest:${env.ARCH}"
                    args """-u 0"""
                    reuseNode true
                }
            }
            options {
                timeout(time: 20, unit: 'MINUTES')
            }
            steps {
                script {
                    cid = sh(
                        script: 'hostname',
                        returnStdout: true
                    ).trim()
                    options = """
                        |-e CI=true
                        |--volumes-from=${cid}
                        |--cpus=1
                        |--memory=2g
                        |--memory-swappiness=0
                        |-v /var/run/docker.sock:/var/run/docker.sock:rw
                        |-v /var/lib/docker/containers:/var/lib/docker/containers:rw
                        |-v /sys/fs/cgroup:/sys/fs/cgroup:ro
                        |-u 0
                    """.stripMargin().stripIndent().replaceAll("[\\t\\n\\r]+"," ").stripMargin().stripIndent()
                    docker.image("jancajthaml/bbtest:${env.ARCH}").withRun(options) { c ->
                        sh "docker exec -t ${c.id} python3 ${env.WORKSPACE}/bbtest/main.py"
                    }
                }
            }
        }

    }

    post {
        always {
            script {
                cucumber(
                    reportTitle: 'Black Box Test',
                    fileIncludePattern: '*',
                    jsonReportDirectory: "${env.WORKSPACE}/reports/blackbox-tests/cucumber"
                )
            }
        }
        success {
            cleanWs()
        }
        failure {
            dir("${env.WORKSPACE}/reports") {
                archiveArtifacts(
                    allowEmptyArchive: true,
                    artifacts: 'blackbox-tests/**/*.log'
                )
            }
            cleanWs()
        }
    }
}
