# OPNFV-Cluster
=========================================================
Enable policy-based clustering service for VNFs in Tacker
=========================================================

https://blueprints.launchpad.net/tacker/+spec/policy-based-vnf-cluster

This spec describes the plan to add VNF high availability deployment and
management function into NFV Orchestrator (NFVO). This function is used
to deploy a cluster of Active and Standby VNFs in order to provide the high
availability for VNF. This function also supports policy-based clustering
management for VNFs.

Problem description
===================

In Telco environment, the reliability of network service (NS) is highly
required. Beside auto-healing and auto-scaling solutions, traditional
redundancy configuration methods, such as Active-Active or Active-Standby
(form a high availability cluster) could be applied to VNFs to ensure the
reliability of the NS. These high availability cluster configurations enable
fast recovery of VNFs operation in case of failure. Operators will need a
way to deploy and manage such kind of high availability clusters via NFVO
component. Refer to ETSI-REL [#first]_ for VNF protection schemes in NFV
system.

The challenge of high availability cluster deployment involves several
requirements that need to be handled by the NFV component as described as
below:

* Resource usage information of each VIM and availability zone for optimal
  cluster member placement
* NFVO should find optimal locations for cluster members (based on predefined
  policies or dynamic network condition and resource usage status)
* Load balancing strategies and monitoring strategies (heartbeat between
  cluster members or from NFVO)

Currently, in Tacker, there is no feature to create and manage such kind of
high availability clusters. With this proposal, we intend to allow Tacker
users to create and manage such kind of high availability clusters. This
function enables Tacker to deploy a cluster of Active and Standby VNFs based
on predefined operator polices. These high availability policies includes VNF
placement locations (i.e. availability zones, VIMs), load balancer
configuration. On the other hand, we also define a new **recovery** actions
which are going to be triggered when failure occurs from cluster members.

Proposed change
===============
The proposed component in NFVO to support high availability cluster management
is shown as below figure:

::

  +--------------------------------------+ +--------------------------+
  |                 NFVO                 | |         VNFM             |
  |                                      | |                          |
  | +-----------------+ +--------------+ | | +-----------------------+|
  | |    HA Policy    | |    Cluster   | | | |      Monitoring       ||
  | |                 | |    engine    | | | |        Driver         ||
  | |                 | | +----------+ | | | |      Framework        ||
  | |                 | | | Cluster  | | | | |                       ||
  | | +-------------+ | | +----------+ | | | |                       ||
  | | |    Role     | | | +----------+ | | | |+-----+  +----+ +----+ ||
  | | |configuration| | | |   VNFD   | | | | ||     |  |    | |    | ||
  | | +-------------+ | | | recovery |<------||Alarm|  |Ping| |HTTP| ||
  | |                 | | +----------+ | | | ||     |  |    | |Ping| ||
  | | +-------------+ | | +----------+ | | | ||     |  |    | |    | ||
  | | |Load balancer| | | | HA Policy| | | | |+-----+  +----+ +----+ ||
  | | |configuration| | | +-----^----+ | | | +-----------------------+|
  | | +-------------+ | |       |      | | |                          |
  | +-----------------+ +-------|------+ | |                          |
  |          |                  |        | |                          |
  |          +------------------+        | |                          |
  +--------------------------------------+ +--------------------------+

