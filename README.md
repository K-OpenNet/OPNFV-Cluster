# OPNFV-Cluster

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
redundancy configuration methods, such as active-active or active-standby
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

![Architecture of HA deployment in Tacker](../master/arch_ha_deployment.PNG)

The high level changes needed to Tacker aim at accommodating a new feature in
VNF cluster management will include changes to Tacker Client and Tacker
Server. The changes include:

* Adding a cluster REST APIs to Tacker Client which a client can use to CRUD
  cluster via command line interface. The client can use the REST APIs to
  deploy VNF cluster from VNFD (from existing VNF will be supported in future).
  The created cluster should include: (1) The created VNFs that are added to
  cluster as cluster members, these VNFs must be deployed from the same VNFD,
  (2) The Neutron load balancer that connects to cluster members aiming at
  loadbalancing traffic among cluster members, and (3) the attached deployment
  policy (Be described in detail as below). The proposed operations are:

  Example of CRUD cluster CLI:

  .. code-block:: console

      tacker cluster-create
      tacker cluster-show
      tacker cluster-list
      tacker cluster-delete

  Example of CRUD cluster-member CLI:

  .. code-block:: console

      tacker cluster-member-add
      tacker cluster-member-show
      tacker cluster-member-list
      tacker cluster-member-delete

* In order to make cluster creation become more flexible, **--policy-file**
  argument is added in cluster-related command, Tacker Client changes will read
  the policy-file and pass the deployment configuration to Tacker Server via
  REST API. The policy should include a role configuration, placement strategies
  attached members, and the load balancer configuration.

* Tacker Server will also need to modify the NFVO extensions and NFVO plugin
  in order to incorporate VNF cluster related operations and resources.

* The drivers for cluster will need to be written in order to handle both of
  cluster CRUD operations.

Note that this spec is supposed to only provide cluster management in
single site, multi-site scenario will be considered in the future.

Alternatives
------------


Data model impact
-----------------

Data model impact includes the creation of  clusters, clustermembers tables

* The clusters table will hold all the relevant attributes of cluster
  resource, while the attributes of the cluster members that belong to the
  created cluster are stored in the clustermembers table and has an
  individual cluster_id attribute which is mapped to the cluster resouces.

* **lb_info** and **role_config** in clusters table will store all of the
  deployment data that are generated during cluster deployment. These
  attributes will be queried during recovery sessioninclude since the Neutron
  load balancer and cluster nodes information are included.

REST API impact
---------------

Because the policy needs to be defined and attached to a cluster, the policy
file needs to be created first, then it will be passed to cluster creation
command as an argument via --policy-file. A typical policy template file is be
shown  as below:

  .. code-block:: yaml

      properties:
        role:
          active:
            VIM0: 1
          standby:
            VIM0: 1
        load_balancer:
          pool:
            protocol: HTTP
            protocol_port: 80
            subnet: subnet_mgmt
            lb_method: ROUND_ROBIN
          vip:
            subnet: subnet_mgmt
            protocol: HTTP
            protocol_port: 80
          target: CP1

The policy contains **role** and **load_balancer** attributes. The **role**
attribute indicates which VIM the VNF should deploy on and which member roles
(Active or Standby) will be taken by VNFs. Note that deployment of cluster over
multi-VIMs is outside of the scope in this spec, but it might be extended to
support multi-VIMs cluster deployment later. The **load_balancer** attribute
contains configured parameters that will be used to invoke Neutron Client for
deploying a Neutron load balancer.

Because the VNF is treated as a cluster member - a basic unit in cluster,
in order to deploy the cluster the VNFD template need to be created by the
client first. There is no extension of the VNFD compared to the original one.
However, in order to archive HA feature for deployed cluster, a new active
whose name is **recovery** need to be defined and declared in VNFD as an
triggred action in the case of failure. A sample of VNFD with **recovery**
action can be seen in the following block:

  .. code-block:: yaml

      tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0

      description: Demo example for VNF cluster
      metadata:
        template_name: sample-tosca-vnfd-cluster

      topology_template:
        node_templates:
          VDU1:
            type: tosca.nodes.nfv.VDU.Tacker
            capabilities:
              nfv_compute:
                properties:
                  num_cpus: 1
                  mem_size: 256 MB
                  disk_size: 1 GB
            properties:
              image: cirros-0.3.5-x86_64-disk
              availability_zone: nova
              mgmt_driver: noop
              monitoring_policy:
                name: ping
                parameters:
                  monitoring_delay: 45
                  count: 3
                  interval: 1
                  timeout: 2
                actions:
                  failure: recovery
              config: |
                param0: key1
                param1: key2

          CP1:
            type: tosca.nodes.nfv.CP.Tacker
            properties:
              management: true
              order: 0
              anti_spoofing_protection: true
            requirements:
              - virtualLink:
                  node: VL1
              - virtualBinding:
                  node: VDU1

          VL1:
            type: tosca.nodes.nfv.VL
            properties:
              network_name: net_mgmt
              vendor: Tacker

Example of cluster creation CLI:
  .. code-block:: console

   tacker cluster-create --vnfd-name vnfd-sample --policy-file policy.yaml
   --name cluster-sample

At cluster creation time, the NFVO plugin will query VNFM to find
available VNFD resouces that exist from provided VNFD ID. It also read
policy file in order to deploy cluster by following the defined configuration.

New 'nfvo' extension will be introduced in Tacker API v1 that implements REST
API end point for clusters and clustermembers resources as described below:

.. csv-table:: **/clusters**
    :header: Attribute Name,Type,Access,Default, Validation Conversion,Des

    id, string (UUID),"RO, All",generated,N/A,identity
    tenant_id, String (UUID), "RW, All", "None, (Required)", uuid, "tenant ID
    to launch vnf-cluster"
    name, string,"RW, All","None, (Required)",string,human-readable name
    description, string, "RW, All", None, string, description of cluster
    status, string, "RO, All", generated, string, Status of created cluster
    vnfd_id, string (UUID), "RO, All", None (Required), uuid, "VNFD ID to use
    to deploy cluster members"
    lb_info, string, "RO, All", "None, (Required)", string, "attributes of
    created load balancer"
    role_config, string, "RO, All", "None, (Required)", string, "role
    configuration of cluster members"

.. csv-table:: **/clustermembers**
    :header: Attribute Name,Type,Access,Default, Validation Conversion,Des

    id,string (UUID),"RO, All",generated,N/A,identity
    tenant_id, String (UUID), "RW, All", "None, (Required)", uuid, "tenant ID
    to launch cluster member"
    name, string,"RW, All","None, (Required)",string,human-readable name
    cluster_id, string (UUID), "RO, All", generated, uuid, "ID of associated
    cluster"
    vnf_id, string (UUID), "RO, All", generated, uuid, "ID of associated vnf"
    mgmt_url, string, "RO, All", generated, string, "Management URL of
    associated vnf"
    role, string, "RW, All", generated, String, Role of member in cluster
    lb_member_id, string (UUID), "RO, All", generated, uuid, "ID of associated
    Neutron load balancer"
    placement_attr, string, "RW, All", None (Required), string, "VIM name where
    cluster members are deployed"

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

There will be changes to python-tackerclient for the end user in order to
manage clusters and cluster-members. The changes will involve adding new shell
extensions to python-tackerclient in order to allow CRUD operations for cluster
and cluster-member.

Performance Impact
------------------

None

Other deployer impact
---------------------

**neutron-lbaas** and **octavia** should be installed to make this feature work
so it is necessary to update the tacker's Devstack installation procedure in
the script and the manual installation guideline. Because **neutron-lbaas**
resources are queried in order to deploy load balancer during cluster
creation by using Neutron client.

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary author and contact.

   longkb <longkb@bka.vn>

   xuan0802 <thespring1989@gmail.com>

Primary assignee:

  longkb <longkb@bka.vn>

  xuan0802 <thespring1989@gmail.com>

